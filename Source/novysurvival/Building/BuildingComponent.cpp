#include "BuildingComponent.h"
#include "BuildInventory.h"
#include "BuildPiece.h"
#include "BuildingSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/HitResult.h"
#include "Engine/OverlapResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

#define LOCTEXT_NAMESPACE "Building"

namespace
{
	const EBuildPieceType PieceCycle[] = {
		EBuildPieceType::Foundation, EBuildPieceType::Floor, EBuildPieceType::Wall,
		EBuildPieceType::Doorway, EBuildPieceType::Door, EBuildPieceType::Roof
	};

	// Mriezka sa uklada na cele cm a stupne, aby klient aj server dostali rovnaky kluc slotu.
	FVector RoundVector(const FVector& V)
	{
		return FVector((double)FMath::RoundToInt(V.X), (double)FMath::RoundToInt(V.Y), (double)FMath::RoundToInt(V.Z));
	}

	float RoundYaw(double Yaw)
	{
		return (float)FMath::RoundToInt(FRotator::NormalizeAxis(Yaw));
	}

	bool SameGrid(const ABuildPiece* Piece, const FBuildRequest& Req)
	{
		return UBuildingSubsystem::MakeKey(Piece->GridOrigin, Piece->GridYaw, FIntVector::ZeroValue, EBuildSlot::Floor)
			== UBuildingSubsystem::MakeKey(Req.GridOrigin, Req.GridYaw, FIntVector::ZeroValue, EBuildSlot::Floor);
	}

	void AddCost(TArray<FBuildCost>& Out, FName ItemID, int32 Amount)
	{
		FBuildCost C;
		C.ItemID = ItemID;
		C.Amount = Amount;
		Out.Add(C);
	}

	FBuildPieceDef MakeDef(EBuildPieceType Type, const FText& Name, float Health, int32 Wood, int32 Stone, int32 Metal)
	{
		FBuildPieceDef D;
		D.Type = Type;
		D.Name = Name;
		D.BaseHealth = Health;
		AddCost(D.WoodCost, TEXT("Wood"), Wood);
		AddCost(D.StoneCost, TEXT("Stone"), Stone);
		AddCost(D.MetalCost, TEXT("Metal"), Metal);
		return D;
	}

	FText TextTooFar()    { return LOCTEXT("TooFar", "Príliš ďaleko"); }
	FText TextNotEnough() { return LOCTEXT("NotEnough", "Nemáš dosť materiálu"); }
}

UBuildingComponent::UBuildingComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork; // az po pohybe kamery
	SetIsReplicatedByDefault(true);

	PieceDefs = {
		MakeDef(EBuildPieceType::Foundation, LOCTEXT("Foundation", "Základ"), 500.f, 40, 60, 20),
		MakeDef(EBuildPieceType::Floor, LOCTEXT("Floor", "Podlaha"), 250.f, 20, 30, 10),
		MakeDef(EBuildPieceType::Wall, LOCTEXT("Wall", "Stena"), 300.f, 30, 45, 15),
		MakeDef(EBuildPieceType::Doorway, LOCTEXT("Doorway", "Zárubňa"), 300.f, 25, 35, 12),
		MakeDef(EBuildPieceType::Door, LOCTEXT("Door", "Dvere"), 200.f, 30, 40, 20),
		MakeDef(EBuildPieceType::Roof, LOCTEXT("Roof", "Strecha"), 300.f, 30, 45, 15)
	};
	TierHealthMultiplier = { 1.f, 2.5f, 5.f };
}

void UBuildingComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bBuildMode || !IsLocal())
	{
		SetBuildMode(false);
		return;
	}

	UpdatePreview();

	if (bShowDebugText && GEngine)
	{
		const FString Status = bPreviewValid ? TEXT("OK") : PreviewProblem.ToString();
		FString Line = FString::Printf(TEXT("STAVANIE: %s  |  %s  |  %s"),
			*GetSelectedName().ToString(), *GetSelectedCostText().ToString(), *Status);
		if (const ABuildPiece* Looked = GetLookedAtPiece())
		{
			const FBuildPieceDef* LookedDef = FindDef(Looked->PieceType);
			const FText LookedName = Looked->PieceType == EBuildPieceType::Prop ? FText::FromName(Looked->ItemID)
				: LookedDef ? LookedDef->Name : UEnum::GetDisplayValueAsText(Looked->PieceType);
			Line += FString::Printf(TEXT("\nMieriš na: %s (%s) %d/%d HP"),
				*LookedName.ToString(), *Looked->GetTierName().ToString(),
				FMath::CeilToInt(Looked->Health), FMath::CeilToInt(Looked->MaxHealth));
		}
		GEngine->AddOnScreenDebugMessage((uint64)GetUniqueID(), 0.f, bPreviewValid ? FColor::Cyan : FColor::Orange, Line);
	}
}

void UBuildingComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	DestroyPreview();
	Super::EndPlay(Reason);
}

// ---------------------------------------------------------------------------
// Vstupy
// ---------------------------------------------------------------------------

void UBuildingComponent::ToggleBuildMode()
{
	SetBuildMode(!bBuildMode);
}

void UBuildingComponent::SetBuildMode(bool bEnable)
{
	if (bEnable && !IsLocal())
	{
		return;
	}
	bBuildMode = bEnable;
	SetComponentTickEnabled(bEnable);
	if (!bEnable)
	{
		DestroyPreview();
		bPreviewValid = false;
		PreviewProblem = FText::GetEmpty();
	}
}

void UBuildingComponent::SelectPiece(EBuildPieceType Type)
{
	if (Type == EBuildPieceType::Prop && SelectedPropItem.IsNone())
	{
		return;
	}
	SelectedType = Type;
	RotationIndex = 0;
}

void UBuildingComponent::SelectNextPiece(int32 Direction)
{
	const int32 Num = UE_ARRAY_COUNT(PieceCycle);
	int32 Index = INDEX_NONE;
	for (int32 i = 0; i < Num; ++i)
	{
		if (PieceCycle[i] == SelectedType)
		{
			Index = i;
		}
	}
	Index = Index == INDEX_NONE ? 0 : (Index + (Direction >= 0 ? 1 : -1) + Num) % Num;
	SelectPiece(PieceCycle[Index]);
}

void UBuildingComponent::SelectProp(FName ItemID)
{
	if (ItemID.IsNone())
	{
		return;
	}
	SelectedPropItem = ItemID;
	SelectedType = EBuildPieceType::Prop;
	RotationIndex = 0;
	SetBuildMode(true);
}

void UBuildingComponent::RotatePreview()
{
	RotationIndex = (RotationIndex + 1) % 8;
}

void UBuildingComponent::TryPlace()
{
	if (!bBuildMode || !IsLocal())
	{
		return;
	}
	const double Now = GetWorld()->GetTimeSeconds();
	if (Now - LastPlaceTime < 0.2)
	{
		return;
	}
	if (!bPreviewValid)
	{
		if (!PreviewProblem.IsEmpty())
		{
			ShowMessage(PreviewProblem);
		}
		return;
	}
	LastPlaceTime = Now;
	ServerPlace(CurrentRequest);

	// predmet z inventara sa polozi raz, potom sa rezim stavania vypne
	if (CurrentRequest.Type == EBuildPieceType::Prop)
	{
		SelectedType = EBuildPieceType::Foundation;
		SelectedPropItem = NAME_None;
		SetBuildMode(false);
	}
}

void UBuildingComponent::TryDemolish()
{
	if (!bBuildMode || !IsLocal())
	{
		return;
	}
	if (ABuildPiece* Piece = GetLookedAtPiece())
	{
		ServerDemolish(Piece);
	}
}

void UBuildingComponent::TryUpgrade()
{
	if (!bBuildMode || !IsLocal())
	{
		return;
	}
	ABuildPiece* Piece = GetLookedAtPiece();
	if (Piece && Piece->PieceType != EBuildPieceType::Prop)
	{
		ServerUpgrade(Piece);
	}
}

void UBuildingComponent::TryInteract()
{
	if (!IsLocal())
	{
		return;
	}
	ABuildPiece* Piece = GetLookedAtPiece();
	if (!Piece)
	{
		return;
	}
	// mierenie na zarubnu otvori dvere v nej
	if (Piece->PieceType == EBuildPieceType::Doorway)
	{
		UBuildingSubsystem* Sub = GetSubsystem();
		const EBuildSlot DoorSlot = Piece->Slot == EBuildSlot::EdgeX ? EBuildSlot::DoorX : EBuildSlot::DoorY;
		Piece = Sub ? Sub->GetPiece(Piece->GridOrigin, Piece->GridYaw, Piece->Cell, DoorSlot) : nullptr;
	}
	if (Piece && Piece->PieceType == EBuildPieceType::Door)
	{
		ServerInteract(Piece);
	}
}

// ---------------------------------------------------------------------------
// HUD
// ---------------------------------------------------------------------------

FText UBuildingComponent::GetSelectedName() const
{
	if (SelectedType == EBuildPieceType::Prop)
	{
		return FText::FromName(SelectedPropItem);
	}
	const FBuildPieceDef* Def = FindDef(SelectedType);
	return Def ? Def->Name : FText::GetEmpty();
}

FText UBuildingComponent::GetSelectedCostText() const
{
	if (bFreeBuild)
	{
		return LOCTEXT("Free", "zadarmo");
	}
	FBuildRequest Req;
	Req.Type = SelectedType;
	Req.ItemID = SelectedPropItem;
	TArray<FString> Parts;
	for (const FBuildCost& C : GetPlaceCost(Req))
	{
		Parts.Add(FString::Printf(TEXT("%s x%d"), *C.ItemID.ToString(), C.Amount));
	}
	return FText::FromString(FString::Join(Parts, TEXT(", ")));
}

ABuildPiece* UBuildingComponent::GetLookedAtPiece() const
{
	FHitResult Hit;
	FVector ViewLoc;
	FRotator ViewRot;
	if (!TraceView(Hit, ViewLoc, ViewRot))
	{
		return nullptr;
	}
	ABuildPiece* Piece = Cast<ABuildPiece>(Hit.GetActor());
	return (Piece && !Piece->IsPreview() && !Piece->IsActorBeingDestroyed()) ? Piece : nullptr;
}

// ---------------------------------------------------------------------------
// Pomocne
// ---------------------------------------------------------------------------

APawn* UBuildingComponent::GetPawn() const
{
	if (APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		return Pawn;
	}
	if (const APlayerController* PC = Cast<APlayerController>(GetOwner()))
	{
		return PC->GetPawn();
	}
	return nullptr;
}

APlayerController* UBuildingComponent::GetPC() const
{
	if (APlayerController* PC = Cast<APlayerController>(GetOwner()))
	{
		return PC;
	}
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		return Cast<APlayerController>(Pawn->GetController());
	}
	return nullptr;
}

bool UBuildingComponent::IsLocal() const
{
	const APlayerController* PC = GetPC();
	return PC && PC->IsLocalController() && GetPawn();
}

UBuildingSubsystem* UBuildingComponent::GetSubsystem() const
{
	UWorld* World = GetWorld();
	return World ? World->GetSubsystem<UBuildingSubsystem>() : nullptr;
}

const FBuildPieceDef* UBuildingComponent::FindDef(EBuildPieceType Type) const
{
	for (const FBuildPieceDef& Def : PieceDefs)
	{
		if (Def.Type == Type)
		{
			return &Def;
		}
	}
	return nullptr;
}

float UBuildingComponent::GetMaxHealth(EBuildPieceType Type, EBuildTier Tier) const
{
	const FBuildPieceDef* Def = FindDef(Type);
	const float Base = Def ? Def->BaseHealth : 100.f;
	const int32 Index = (int32)Tier;
	return Base * (TierHealthMultiplier.IsValidIndex(Index) ? TierHealthMultiplier[Index] : 1.f);
}

TArray<FBuildCost> UBuildingComponent::GetPlaceCost(const FBuildRequest& Req) const
{
	TArray<FBuildCost> Costs;
	if (Req.Type == EBuildPieceType::Prop)
	{
		if (!Req.ItemID.IsNone())
		{
			AddCost(Costs, Req.ItemID, 1);
		}
	}
	else if (const FBuildPieceDef* Def = FindDef(Req.Type))
	{
		Costs = Def->GetCost(EBuildTier::Wood); // stavia sa z dreva, potom sa vylepsuje
	}
	return Costs;
}

bool UBuildingComponent::TraceView(FHitResult& OutHit, FVector& OutViewLoc, FRotator& OutViewRot) const
{
	OutViewLoc = FVector::ZeroVector;
	OutViewRot = FRotator::ZeroRotator;
	APlayerController* PC = GetPC();
	APawn* Pawn = GetPawn();
	UWorld* World = GetWorld();
	if (!PC || !Pawn || !World)
	{
		return false;
	}
	PC->GetPlayerViewPoint(OutViewLoc, OutViewRot);

	// pri tretej osobe je kamera za postavou – luc sa predlzi o tuto vzdialenost
	const double Length = BuildRange + FVector::Dist(OutViewLoc, Pawn->GetPawnViewLocation());

	FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildTrace), false, Pawn);
	TArray<AActor*> Attached;
	Pawn->GetAttachedActors(Attached);
	Params.AddIgnoredActors(Attached);
	if (Preview)
	{
		Params.AddIgnoredActor(Preview);
	}
	return World->LineTraceSingleByChannel(OutHit, OutViewLoc, OutViewLoc + OutViewRot.Vector() * Length, ECC_Visibility, Params);
}

ABuildPiece* UBuildingComponent::FindGridPiece(const FHitResult& Hit) const
{
	if (ABuildPiece* Piece = Cast<ABuildPiece>(Hit.GetActor()))
	{
		if (Piece->IsInGrid() && !Piece->IsActorBeingDestroyed())
		{
			return Piece;
		}
	}

	// mierim na zem vedla stavby -> prichyt sa k najblizsiemu dielu
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	FCollisionObjectQueryParams ObjParams;
	ObjParams.AddObjectTypesToQuery(ECC_WorldStatic);
	ObjParams.AddObjectTypesToQuery(ECC_WorldDynamic);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildFindGrid), false, GetPawn());
	TArray<FOverlapResult> Overlaps;
	World->OverlapMultiByObjectType(Overlaps, Hit.ImpactPoint, FQuat::Identity, ObjParams, FCollisionShape::MakeSphere(BuildGrid::Cell * 1.5f), Params);

	ABuildPiece* Best = nullptr;
	double BestDist = TNumericLimits<double>::Max();
	for (const FOverlapResult& O : Overlaps)
	{
		ABuildPiece* Piece = Cast<ABuildPiece>(O.GetActor());
		if (!Piece || !Piece->IsInGrid() || Piece->IsActorBeingDestroyed())
		{
			continue;
		}
		const double Dist = FVector::DistSquared(Piece->GetActorLocation(), FVector(Hit.ImpactPoint));
		if (Dist < BestDist)
		{
			BestDist = Dist;
			Best = Piece;
		}
	}
	return Best;
}

// ---------------------------------------------------------------------------
// Kam sa diel polozi
// ---------------------------------------------------------------------------

bool UBuildingComponent::ComputeRequest(FBuildRequest& Req, FTransform& OutTransform) const
{
	Req = FBuildRequest();
	Req.Type = SelectedType;
	Req.ItemID = SelectedType == EBuildPieceType::Prop ? SelectedPropItem : NAME_None;

	FHitResult Hit;
	FVector ViewLoc;
	FRotator ViewRot;
	const bool bHit = TraceView(Hit, ViewLoc, ViewRot);
	const float ViewYaw = (float)ViewRot.Yaw;
	const FVector Point = bHit ? FVector(Hit.ImpactPoint) : ViewLoc + ViewRot.Vector() * BuildRange;
	OutTransform = FTransform(FRotator(0.f, ViewYaw, 0.f), Point);

	// Predmet z inventara: volne na rovny povrch, otoceny k hracovi.
	if (Req.Type == EBuildPieceType::Prop)
	{
		Req.bSnapped = false;
		Req.FreeLocation = Point;
		Req.FreeYaw = RoundYaw(ViewYaw + 180.f + RotationIndex * 45.f);
		OutTransform = FTransform(FRotator(0.f, Req.FreeYaw, 0.f), Req.FreeLocation);
		return bHit && Hit.ImpactNormal.Z > 0.7f;
	}

	UBuildingSubsystem* Sub = GetSubsystem();
	if (!bHit || !Sub)
	{
		return false;
	}

	ABuildPiece* GridPiece = FindGridPiece(Hit);
	if (!GridPiece)
	{
		// Bez stavby v okoli sa da polozit len zaklad – zacne novu mriezku.
		if (Req.Type != EBuildPieceType::Foundation)
		{
			return false;
		}
		Req.GridOrigin = RoundVector(Point + FVector(0.f, 0.f, BuildGrid::FoundationHeight * 0.5f));
		Req.GridYaw = RoundYaw(ViewYaw + RotationIndex * 45.f);
		Req.Cell = FIntVector::ZeroValue;
		Req.Slot = EBuildSlot::Floor;
		OutTransform = BuildGrid::SlotTransform(Req.GridOrigin, Req.GridYaw, Req.Cell, Req.Slot, 0);
		return true;
	}

	// diel, na ktory hrac priamo miery (ak je v tej istej mriezke)
	const ABuildPiece* Aimed = GridPiece == Hit.GetActor() ? GridPiece : nullptr;
	const FVector Origin = GridPiece->GridOrigin;
	const float Yaw = GridPiece->GridYaw;
	Req.GridOrigin = Origin;
	Req.GridYaw = Yaw;

	// bod tesne pred zasiahnutym povrchom a kamera v suradniciach mriezky
	const FVector P = BuildGrid::WorldToLocal(Origin, Yaw, FVector(Hit.ImpactPoint) + FVector(Hit.ImpactNormal) * 2.f);
	const FVector Cam = BuildGrid::WorldToLocal(Origin, Yaw, ViewLoc);
	const double GX = P.X / BuildGrid::Cell;
	const double GY = P.Y / BuildGrid::Cell;
	const int32 CX = FMath::RoundToInt(GX);
	const int32 CY = FMath::RoundToInt(GY);
	const double FX = GX - CX; // -0.5..0.5 v ramci bunky
	const double FY = GY - CY;

	switch (Req.Type)
	{
	case EBuildPieceType::Foundation:
	case EBuildPieceType::Floor:
	case EBuildPieceType::Roof:
	{
		FIntVector C = FIntVector::ZeroValue;
		if (Aimed && Aimed->Slot != EBuildSlot::Floor && Req.Type != EBuildPieceType::Foundation)
		{
			// na vrch steny / zarubne, na tu stranu, kde stoji hrac
			const bool bAlongX = Aimed->Slot == EBuildSlot::EdgeX || Aimed->Slot == EBuildSlot::DoorX;
			const FIntVector Across = bAlongX ? FIntVector(1, 0, 0) : FIntVector(0, 1, 0);
			C = Aimed->Cell + FIntVector(0, 0, 1);
			if (FVector::DistSquared2D(Cam, BuildGrid::CellCenter(C + Across)) < FVector::DistSquared2D(Cam, BuildGrid::CellCenter(C)))
			{
				C = C + Across;
			}
		}
		else
		{
			int32 CZ = 0;
			if (Req.Type != EBuildPieceType::Foundation)
			{
				CZ = Aimed ? Aimed->Cell.Z : FMath::Max(0, FMath::RoundToInt(P.Z / BuildGrid::Height));
			}
			C = FIntVector(CX, CY, CZ);
			if (!Sub->IsFree(Origin, Yaw, C, EBuildSlot::Floor))
			{
				// miery na vrch existujucej podlahy -> susedna bunka za blizsou hranou
				if (FMath::Abs(FX) >= FMath::Abs(FY))
				{
					C.X += FX >= 0.0 ? 1 : -1;
				}
				else
				{
					C.Y += FY >= 0.0 ? 1 : -1;
				}
			}
		}
		Req.Cell = C;
		Req.Slot = EBuildSlot::Floor;
		if (Req.Type == EBuildPieceType::Roof)
		{
			// strecha stupa smerom od hraca, R ju otaca
			const FVector ToCell = BuildGrid::CellCenter(C) - Cam;
			const int32 Base = FMath::Abs(ToCell.X) >= FMath::Abs(ToCell.Y) ? (ToCell.X >= 0.0 ? 0 : 2) : (ToCell.Y >= 0.0 ? 1 : 3);
			Req.RoofDir = (Base + RotationIndex) % 4;
		}
		break;
	}
	case EBuildPieceType::Wall:
	case EBuildPieceType::Doorway:
	case EBuildPieceType::Door:
	{
		if (Req.Type == EBuildPieceType::Door && Aimed
			&& (Aimed->PieceType == EBuildPieceType::Doorway || Aimed->PieceType == EBuildPieceType::Door))
		{
			const bool bAlongX = Aimed->Slot == EBuildSlot::EdgeX || Aimed->Slot == EBuildSlot::DoorX;
			Req.Cell = Aimed->Cell;
			Req.Slot = bAlongX ? EBuildSlot::DoorX : EBuildSlot::DoorY;
		}
		else
		{
			// najblizsia hrana bunky
			const int32 CZ = FMath::Max(0, FMath::FloorToInt(P.Z / BuildGrid::Height));
			if (FMath::Abs(FX) >= FMath::Abs(FY))
			{
				Req.Slot = EBuildSlot::EdgeX;
				Req.Cell = FIntVector(FX >= 0.0 ? CX : CX - 1, CY, CZ);
			}
			else
			{
				Req.Slot = EBuildSlot::EdgeY;
				Req.Cell = FIntVector(CX, FY >= 0.0 ? CY : CY - 1, CZ);
			}
			if (Req.Type == EBuildPieceType::Door)
			{
				Req.Slot = Req.Slot == EBuildSlot::EdgeX ? EBuildSlot::DoorX : EBuildSlot::DoorY;
			}
		}
		if (Req.Type == EBuildPieceType::Door)
		{
			Req.RoofDir = RotationIndex & 1; // R prehodi stranu pantu
		}
		break;
	}
	default:
		return false;
	}

	OutTransform = BuildGrid::SlotTransform(Req.GridOrigin, Req.GridYaw, Req.Cell, Req.Slot, Req.RoofDir);
	return true;
}

// ---------------------------------------------------------------------------
// Kontroly (klient pre nahlad, server naozaj)
// ---------------------------------------------------------------------------

bool UBuildingComponent::CheckPlacement(const FBuildRequest& Req, FTransform& OutTransform, FText& OutProblem) const
{
	UBuildingSubsystem* Sub = GetSubsystem();
	if (!Sub)
	{
		return false;
	}

	if (Req.Type == EBuildPieceType::Prop)
	{
		OutTransform = FTransform(FRotator(0.f, Req.FreeYaw, 0.f), Req.FreeLocation);
		if (!PropMeshes.FindRef(Req.ItemID))
		{
			OutProblem = LOCTEXT("NoProp", "Tento predmet sa nedá položiť");
			return false;
		}
		if (!IsInRange(Req.FreeLocation))
		{
			OutProblem = TextTooFar();
			return false;
		}
		FHitResult Ground;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildPropGround), false, GetPawn());
		if (Preview)
		{
			Params.AddIgnoredActor(Preview);
		}
		if (!GetWorld()->LineTraceSingleByChannel(Ground, Req.FreeLocation + FVector(0.f, 0.f, 20.f), Req.FreeLocation - FVector(0.f, 0.f, 30.f), ECC_Visibility, Params))
		{
			OutProblem = LOCTEXT("PropAir", "Musí stáť na zemi");
			return false;
		}
		if (IsBlocked(Req, OutTransform))
		{
			OutProblem = LOCTEXT("Blocked", "Niečo zavadzia");
			return false;
		}
		return true;
	}

	if (!FindDef(Req.Type) || !BuildGrid::SlotMatchesType(Req.Type, Req.Slot)
		|| (Req.Type == EBuildPieceType::Foundation && Req.Cell.Z != 0))
	{
		OutProblem = LOCTEXT("BadRequest", "Sem sa to nedá");
		return false;
	}

	OutTransform = BuildGrid::SlotTransform(Req.GridOrigin, Req.GridYaw, Req.Cell, Req.Slot, Req.RoofDir);
	if (!IsInRange(OutTransform.GetLocation()))
	{
		OutProblem = TextTooFar();
		return false;
	}
	if (!Sub->IsFree(Req.GridOrigin, Req.GridYaw, Req.Cell, Req.Slot))
	{
		OutProblem = LOCTEXT("Occupied", "Miesto je obsadené");
		return false;
	}
	if (!Sub->IsSupported(Req.GridOrigin, Req.GridYaw, Req.Cell, Req.Slot, Req.Type))
	{
		OutProblem = Req.Type == EBuildPieceType::Door
			? LOCTEXT("NeedDoorway", "Dvere patria do zárubne")
			: LOCTEXT("NoSupport", "Nič to nedrží");
		return false;
	}
	if (Req.Type == EBuildPieceType::Foundation && !IsGrounded(OutTransform.GetLocation()))
	{
		OutProblem = LOCTEXT("NotGrounded", "Základ musí byť na zemi");
		return false;
	}
	if (IsBlocked(Req, OutTransform))
	{
		OutProblem = LOCTEXT("Blocked", "Niečo zavadzia");
		return false;
	}
	return true;
}

bool UBuildingComponent::IsInRange(const FVector& Location) const
{
	const APawn* Pawn = GetPawn();
	return Pawn && FVector::Dist(Pawn->GetPawnViewLocation(), Location) <= BuildRange + BuildGrid::Cell;
}

bool UBuildingComponent::IsGrounded(const FVector& TopCenter) const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}
	// pod stredom zakladu musi byt teren: nie hlboko pod nim a nie nad jeho vrchom
	const FVector Start = TopCenter + FVector(0.f, 0.f, 200.f);
	const FVector End = TopCenter - FVector(0.f, 0.f, BuildGrid::FoundationHeight + 150.f);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildGround), false, GetPawn());
	if (Preview)
	{
		Params.AddIgnoredActor(Preview);
	}
	for (int32 i = 0; i < 8; ++i)
	{
		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
		{
			return false;
		}
		AActor* A = Hit.GetActor();
		if (A && (A->IsA<ABuildPiece>() || A->IsA<APawn>()))
		{
			Params.AddIgnoredActor(A);
			continue;
		}
		return Hit.ImpactPoint.Z <= TopCenter.Z + 30.f;
	}
	return false;
}

bool UBuildingComponent::IsBlocked(const FBuildRequest& Req, const FTransform& Transform) const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return true;
	}

	const bool bProp = Req.Type == EBuildPieceType::Prop;
	TArray<FBuildBox> Boxes;
	if (bProp)
	{
		if (UStaticMesh* Mesh = PropMeshes.FindRef(Req.ItemID))
		{
			const FBox Bounds = Mesh->GetBoundingBox();
			Boxes.Add({ Bounds.GetCenter(), Bounds.GetSize() });
		}
	}
	else
	{
		BuildGrid::GetShape(Req.Type, Boxes);
	}

	FCollisionObjectQueryParams ObjParams;
	ObjParams.AddObjectTypesToQuery(ECC_WorldStatic);
	ObjParams.AddObjectTypesToQuery(ECC_WorldDynamic);
	ObjParams.AddObjectTypesToQuery(ECC_Pawn);
	ObjParams.AddObjectTypesToQuery(ECC_PhysicsBody);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(BuildOverlap), false);
	if (Preview)
	{
		Params.AddIgnoredActor(Preview);
	}

	for (const FBuildBox& Box : Boxes)
	{
		FVector Center = Box.Center;
		if (Req.Type == EBuildPieceType::Door)
		{
			Center.X -= BuildGrid::DoorWidth * 0.5f; // tvar dveri je relativne k pantu
		}
		// o kusok mensi box, aby susedne diely, co sa len dotykaju, nevadili
		const FVector Half = (Box.Size * 0.5f - FVector(10.f)).ComponentMax(FVector(2.f));
		TArray<FOverlapResult> Overlaps;
		World->OverlapMultiByObjectType(Overlaps, Transform.TransformPosition(Center), Transform.GetRotation() * Box.Rot.Quaternion(),
			ObjParams, FCollisionShape::MakeBox(Half), Params);

		for (const FOverlapResult& O : Overlaps)
		{
			const AActor* A = O.GetActor();
			if (!A)
			{
				continue;
			}
			if (A->IsA<APawn>())
			{
				return true; // hrac alebo zviera v ceste
			}
			const ABuildPiece* Piece = Cast<ABuildPiece>(A);
			if (!Piece || Piece->IsPreview() || Piece->IsActorBeingDestroyed())
			{
				continue; // teren, skaly... nevadia
			}
			if (!Piece->IsInGrid())
			{
				return true; // polozeny predmet
			}
			if (!bProp && !SameGrid(Piece, Req))
			{
				return true; // cudzia stavba
			}
		}
	}
	return false;
}

// ---------------------------------------------------------------------------
// Nahlad
// ---------------------------------------------------------------------------

void UBuildingComponent::UpdatePreview()
{
	FBuildRequest Req;
	FTransform Transform;
	const bool bTarget = ComputeRequest(Req, Transform);

	UStaticMesh* Mesh = Req.Type == EBuildPieceType::Prop ? PropMeshes.FindRef(Req.ItemID).Get() : nullptr;
	if (!Preview)
	{
		UWorld* World = GetWorld();
		UClass* Class = PieceClass ? PieceClass.Get() : ABuildPiece::StaticClass();
		Preview = World ? World->SpawnActorDeferred<ABuildPiece>(Class, Transform, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn) : nullptr;
		if (!Preview)
		{
			return;
		}
		Preview->SetReplicates(false); // nahlad vidi len tento hrac
		Preview->SetupPreview(Req.Type, Mesh, GhostMaterial);
		Preview->FinishSpawning(Transform);
		PreviewType = Req.Type;
		PreviewMesh = Mesh;
	}
	else if (PreviewType != Req.Type || PreviewMesh != Mesh)
	{
		Preview->SetupPreview(Req.Type, Mesh, GhostMaterial);
		PreviewType = Req.Type;
		PreviewMesh = Mesh;
	}
	Preview->SetActorTransform(Transform);

	FTransform Checked;
	FText Problem = LOCTEXT("NoTarget", "Namier na zem alebo na stavbu");
	bPreviewValid = bTarget && CheckPlacement(Req, Checked, Problem);
	PreviewProblem = bPreviewValid ? FText::GetEmpty() : Problem;
	Preview->SetPreviewValid(bPreviewValid);
	CurrentRequest = Req;
}

void UBuildingComponent::DestroyPreview()
{
	if (IsValid(Preview))
	{
		Preview->Destroy();
	}
	Preview = nullptr;
	PreviewMesh = nullptr;
}

void UBuildingComponent::ShowMessage(const FText& Message)
{
	OnBuildMessage.Broadcast(Message);
	if (bShowDebugText && GEngine && !Message.IsEmpty())
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Orange, Message.ToString());
	}
}

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------

void UBuildingComponent::ServerPlace_Implementation(const FBuildRequest& InReq)
{
	FBuildRequest Req = InReq;
	if (Req.Type == EBuildPieceType::Prop)
	{
		Req.bSnapped = false;
		Req.FreeYaw = RoundYaw(Req.FreeYaw);
	}
	else
	{
		Req.bSnapped = true;
		Req.ItemID = NAME_None;
		Req.GridOrigin = RoundVector(Req.GridOrigin);
		Req.GridYaw = RoundYaw(Req.GridYaw);
		Req.RoofDir = Req.Type == EBuildPieceType::Roof ? ((Req.RoofDir % 4) + 4) % 4
			: Req.Type == EBuildPieceType::Door ? (Req.RoofDir & 1) : 0;
	}

	FTransform Transform;
	FText Problem;
	if (!CheckPlacement(Req, Transform, Problem))
	{
		ClientBuildMessage(Problem);
		return;
	}

	APlayerController* PC = GetPC();
	const TArray<FBuildCost> Costs = GetPlaceCost(Req);
	if (!bFreeBuild && !FBuildInventory::ConsumeCosts(PC, Costs))
	{
		ClientBuildMessage(TextNotEnough());
		return;
	}

	UStaticMesh* Mesh = Req.Type == EBuildPieceType::Prop ? PropMeshes.FindRef(Req.ItemID).Get() : nullptr;
	const float Health = Req.Type == EBuildPieceType::Prop ? PropHealth : GetMaxHealth(Req.Type, EBuildTier::Wood);
	UClass* Class = PieceClass ? PieceClass.Get() : ABuildPiece::StaticClass();
	ABuildPiece* Piece = GetWorld()->SpawnActorDeferred<ABuildPiece>(Class, Transform, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (!Piece)
	{
		if (!bFreeBuild)
		{
			for (const FBuildCost& C : Costs)
			{
				FBuildInventory::Add(PC, C.ItemID, C.Amount);
			}
		}
		return;
	}
	Piece->InitPiece(Req, EBuildTier::Wood, Health, Mesh);
	Piece->FinishSpawning(Transform);
}

void UBuildingComponent::ServerDemolish_Implementation(ABuildPiece* Piece)
{
	if (!IsValid(Piece) || Piece->IsPreview() || Piece->IsActorBeingDestroyed())
	{
		return;
	}
	if (!IsInRange(Piece->GetActorLocation()))
	{
		ClientBuildMessage(TextTooFar());
		return;
	}

	if (!bFreeBuild)
	{
		APlayerController* PC = GetPC();
		if (Piece->PieceType == EBuildPieceType::Prop)
		{
			if (!Piece->ItemID.IsNone())
			{
				FBuildInventory::Add(PC, Piece->ItemID, 1);
			}
		}
		else if (const FBuildPieceDef* Def = FindDef(Piece->PieceType))
		{
			// poskodeny diel vrati menej
			const float Condition = Piece->MaxHealth > 0.f ? FMath::Clamp(Piece->Health / Piece->MaxHealth, 0.f, 1.f) : 0.f;
			for (const FBuildCost& C : Def->GetCost(Piece->Tier))
			{
				FBuildInventory::Add(PC, C.ItemID, FMath::FloorToInt(C.Amount * DemolishRefund * Condition));
			}
		}
	}
	// EndPlay dielu spusti kontrolu statiky – co uz nic nedrzi, spadne
	Piece->Destroy();
}

void UBuildingComponent::ServerUpgrade_Implementation(ABuildPiece* Piece)
{
	if (!IsValid(Piece) || Piece->IsPreview() || Piece->IsActorBeingDestroyed() || Piece->PieceType == EBuildPieceType::Prop)
	{
		return;
	}
	if (!IsInRange(Piece->GetActorLocation()))
	{
		ClientBuildMessage(TextTooFar());
		return;
	}
	if (Piece->Tier == EBuildTier::Metal)
	{
		ClientBuildMessage(LOCTEXT("MaxTier", "Už je z najlepšieho materiálu"));
		return;
	}
	const FBuildPieceDef* Def = FindDef(Piece->PieceType);
	if (!Def)
	{
		return;
	}
	const EBuildTier Next = static_cast<EBuildTier>(static_cast<uint8>(Piece->Tier) + 1);
	if (!bFreeBuild && !FBuildInventory::ConsumeCosts(GetPC(), Def->GetCost(Next)))
	{
		ClientBuildMessage(TextNotEnough());
		return;
	}
	Piece->SetTier(Next, GetMaxHealth(Piece->PieceType, Next));
	ClientBuildMessage(FText::Format(LOCTEXT("Upgraded", "Vylepšené: {0}"), Piece->GetTierName()));
}

void UBuildingComponent::ServerInteract_Implementation(ABuildPiece* Piece)
{
	if (IsValid(Piece) && !Piece->IsPreview() && Piece->PieceType == EBuildPieceType::Door && IsInRange(Piece->GetActorLocation()))
	{
		Piece->ToggleDoor();
	}
}

void UBuildingComponent::ClientBuildMessage_Implementation(const FText& Message)
{
	ShowMessage(Message);
}

#undef LOCTEXT_NAMESPACE
