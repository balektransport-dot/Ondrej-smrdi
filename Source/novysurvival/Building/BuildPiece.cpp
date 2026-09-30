#include "BuildPiece.h"
#include "BuildingSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/DamageEvents.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	constexpr int32 NumBoxParts = 3; // Parts[0..2] na Root, Parts[3] = dverove kridlo na pante
	const FName ColorParam(TEXT("Color"));
}

ABuildPiece::ABuildPiece()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	SetNetUpdateFrequency(10.f);

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Hinge = CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));
	Hinge->SetupAttachment(Root);

	for (int32 i = 0; i < NumBoxParts + 1; ++i)
	{
		UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("Part%d"), i));
		Part->SetupAttachment(i < NumBoxParts ? Root.Get() : Hinge.Get());
		Part->SetCollisionProfileName(TEXT("BlockAll"));
		Part->SetCanEverAffectNavigation(true);
		Parts.Add(Part);
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	CubeMesh = CubeFinder.Object;

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MatFinder(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	BaseMaterial = MatFinder.Object;

	TierColors = {
		FLinearColor(0.40f, 0.24f, 0.10f), // drevo
		FLinearColor(0.45f, 0.45f, 0.43f), // kamen
		FLinearColor(0.22f, 0.26f, 0.30f)  // kov
	};
}

void ABuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ABuildPiece, PieceType);
	DOREPLIFETIME(ABuildPiece, Tier);
	DOREPLIFETIME(ABuildPiece, Health);
	DOREPLIFETIME(ABuildPiece, MaxHealth);
	DOREPLIFETIME(ABuildPiece, bDoorOpen);
	DOREPLIFETIME(ABuildPiece, GridOrigin);
	DOREPLIFETIME(ABuildPiece, GridYaw);
	DOREPLIFETIME(ABuildPiece, Cell);
	DOREPLIFETIME(ABuildPiece, Slot);
	DOREPLIFETIME(ABuildPiece, RoofDir);
	DOREPLIFETIME(ABuildPiece, ItemID);
	DOREPLIFETIME(ABuildPiece, PropMesh);
}

void ABuildPiece::InitPiece(const FBuildRequest& Req, EBuildTier InTier, float InMaxHealth, UStaticMesh* InPropMesh)
{
	PieceType = Req.Type;
	Tier = InTier;
	MaxHealth = Health = InMaxHealth;
	ItemID = Req.ItemID;
	PropMesh = InPropMesh;
	if (Req.Type == EBuildPieceType::Prop)
	{
		Slot = EBuildSlot::None;
	}
	else
	{
		GridOrigin = Req.GridOrigin;
		GridYaw = Req.GridYaw;
		Cell = Req.Cell;
		Slot = Req.Slot;
		RoofDir = Req.RoofDir;
	}
}

void ABuildPiece::BeginPlay()
{
	Super::BeginPlay();
	RebuildVisual();
	OnRep_Door();

	if (IsInGrid())
	{
		if (UBuildingSubsystem* Sub = GetWorld()->GetSubsystem<UBuildingSubsystem>())
		{
			Sub->Register(this);
			bRegistered = true;
		}
	}
}

void ABuildPiece::EndPlay(const EEndPlayReason::Type Reason)
{
	if (bRegistered)
	{
		if (UBuildingSubsystem* Sub = GetWorld()->GetSubsystem<UBuildingSubsystem>())
		{
			Sub->Unregister(this);
			// Na serveri skontroluj, ci susedne diely este nieco drzi.
			if (HasAuthority() && Reason == EEndPlayReason::Destroyed)
			{
				Sub->QueueStabilityCheck(GridOrigin, GridYaw, Cell);
			}
		}
		bRegistered = false;
	}
	Super::EndPlay(Reason);
}

float ABuildPiece::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (!HasAuthority() || bPreview || DamageAmount <= 0.f)
	{
		return 0.f;
	}
	Health = FMath::Max(0.f, Health - DamageAmount);
	if (Health <= 0.f)
	{
		Destroy();
	}
	return DamageAmount;
}

void ABuildPiece::SetupPreview(EBuildPieceType InType, UStaticMesh* InPropMesh, UMaterialInterface* GhostMaterial)
{
	bPreview = true;
	PieceType = InType;
	PropMesh = InPropMesh;
	// Bez vlastneho priehladneho materialu pouzi zakladny (nahlad bude plny, ale farebny).
	UMaterialInterface* GhostSource = GhostMaterial ? GhostMaterial : BaseMaterial.Get();
	if (!GhostMID && GhostSource)
	{
		GhostMID = UMaterialInstanceDynamic::Create(GhostSource, this);
	}
	RebuildVisual();
}

void ABuildPiece::SetPreviewValid(bool bValid)
{
	if (GhostMID)
	{
		GhostMID->SetVectorParameterValue(ColorParam, bValid ? FLinearColor(0.1f, 0.5f, 1.f) : FLinearColor(1.f, 0.1f, 0.05f));
	}
}

void ABuildPiece::SetTier(EBuildTier NewTier, float NewMaxHealth)
{
	Tier = NewTier;
	MaxHealth = Health = NewMaxHealth;
	ApplyMaterials();
}

void ABuildPiece::ToggleDoor()
{
	bDoorOpen = !bDoorOpen;
	OnRep_Door();
}

FText ABuildPiece::GetTierName() const
{
	switch (Tier)
	{
	case EBuildTier::Stone: return NSLOCTEXT("Build", "Stone", "Kameň");
	case EBuildTier::Metal: return NSLOCTEXT("Build", "Metal", "Kov");
	default:                return NSLOCTEXT("Build", "Wood", "Drevo");
	}
}

void ABuildPiece::OnRep_Visual()
{
	RebuildVisual();
}

void ABuildPiece::OnRep_Door()
{
	Hinge->SetRelativeRotation(FRotator(0.f, bDoorOpen ? 95.f : 0.f, 0.f));
}

void ABuildPiece::RebuildVisual()
{
	TArray<FBuildBox> Boxes;
	BuildGrid::GetShape(PieceType, Boxes);

	const bool bDoor = PieceType == EBuildPieceType::Door;
	const bool bProp = PieceType == EBuildPieceType::Prop;
	Hinge->SetRelativeLocation(FVector(bDoor ? -BuildGrid::DoorWidth * 0.5f : 0.f, 0.f, 0.f));

	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		UStaticMeshComponent* Part = Parts[i];
		bool bUsed = false;

		if (bProp)
		{
			if (i == 0 && PropMesh)
			{
				Part->SetStaticMesh(PropMesh);
				Part->SetRelativeTransform(FTransform::Identity);
				bUsed = true;
			}
		}
		else
		{
			// dvere pouzivaju len Part na pante, ostatne len Parts[0..2]
			const int32 BoxIndex = bDoor ? (i == NumBoxParts ? 0 : INDEX_NONE) : (i < NumBoxParts ? i : INDEX_NONE);
			if (Boxes.IsValidIndex(BoxIndex))
			{
				const FBuildBox& B = Boxes[BoxIndex];
				Part->SetStaticMesh(CubeMesh);
				Part->SetRelativeTransform(FTransform(B.Rot, B.Center, B.Size / 100.f));
				bUsed = true;
			}
		}

		Part->SetVisibility(bUsed);
		Part->SetCollisionEnabled(bUsed && !bPreview ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
		Part->SetCastShadow(!bPreview);
	}

	ApplyMaterials();
}

void ABuildPiece::ApplyMaterials()
{
	UMaterialInterface* Mat = nullptr;
	if (bPreview)
	{
		Mat = GhostMID;
	}
	else if (PieceType != EBuildPieceType::Prop)
	{
		if (!TierMID && BaseMaterial)
		{
			TierMID = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		}
		if (TierMID)
		{
			const int32 Index = FMath::Clamp((int32)Tier, 0, TierColors.Num() - 1);
			TierMID->SetVectorParameterValue(ColorParam, TierColors.IsValidIndex(Index) ? TierColors[Index] : FLinearColor::Gray);
		}
		Mat = TierMID;
	}

	if (!Mat)
	{
		return; // Prop si necha vlastne materialy
	}
	for (UStaticMeshComponent* Part : Parts)
	{
		const int32 Num = FMath::Max(1, Part->GetNumMaterials());
		for (int32 m = 0; m < Num; ++m)
		{
			Part->SetMaterial(m, Mat);
		}
	}
}
