#include "DigSite.h"
#include "DirtContainerComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	constexpr float Density = 1.6f;     // t na m3
	constexpr float HeightRatio = 0.6f; // vyska / polomer kopy
	constexpr float MinDirt = 0.05f;    // mensia kopa zmizne
}

ADigSite::ADigSite()
{
	PrimaryActorTick.bCanEverTick = false;
	bReplicates = true;
	SetNetUpdateFrequency(10.f);

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	// Kuzel enginu: 100 cm vysoky, polomer 50 cm, pivot v strede.
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MatFinder(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	Mound = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mound"));
	Mound->SetupAttachment(Root);
	Mound->SetStaticMesh(ConeFinder.Object);
	Mound->SetMaterial(0, MatFinder.Object);
	Mound->SetCollisionProfileName(TEXT("BlockAll"));
	Mound->SetCollisionResponseToChannel(ECC_Vehicle, ECR_Ignore); // stroje cez kopu prejdu
}

void ADigSite::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ADigSite, Dirt);
	DOREPLIFETIME(ADigSite, Color);
}

void ADigSite::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (!bInitialized)
	{
		Dirt = InitialDirt;
		Gold = InitialDirt * GoldPerTon;
	}
	UpdateShape();
}

void ADigSite::BeginPlay()
{
	Super::BeginPlay();
	bInitialized = true;
	UpdateShape();
}

float ADigSite::GetRadius() const
{
	// objem kuzela V = 1/3 * pi * R^2 * H, H = HeightRatio * R
	const float VolumeM3 = FMath::Max(Dirt, 0.f) / Density;
	const float RadiusM = FMath::Pow(3.f * VolumeM3 / (PI * HeightRatio), 1.f / 3.f);
	return FMath::Max(RadiusM * 100.f, 10.f);
}

float ADigSite::GetHeight() const
{
	return GetRadius() * HeightRatio;
}

FDirtLoad ADigSite::Dig(float Amount)
{
	const float Taken = FMath::Clamp(Amount, 0.f, Dirt);
	if (!HasAuthority() || Taken <= 0.f)
	{
		return FDirtLoad();
	}
	const float GoldTaken = Dirt > 0.f ? Gold * (Taken / Dirt) : 0.f;
	Dirt -= Taken;
	Gold -= GoldTaken;
	if (Dirt < MinDirt)
	{
		Destroy();
	}
	else
	{
		UpdateShape();
	}
	return FDirtLoad(Taken, GoldTaken);
}

void ADigSite::AddLoad(const FDirtLoad& Load)
{
	if (!HasAuthority() || Load.IsEmpty())
	{
		return;
	}
	Dirt += Load.Dirt;
	Gold += Load.Gold;
	UpdateShape();
}

bool ADigSite::ContainsPoint(const FVector& WorldPoint, float Tolerance) const
{
	const FVector Local = WorldPoint - GetActorLocation();
	const float Radius = GetRadius();
	const float Dist = (float)Local.Size2D();
	if (Dist > Radius + Tolerance)
	{
		return false;
	}
	const float Surface = GetHeight() * FMath::Max(0.f, 1.f - Dist / Radius);
	return Local.Z <= Surface + Tolerance && Local.Z >= -150.f;
}

void ADigSite::OnRep_Dirt()
{
	UpdateShape();
}

void ADigSite::UpdateShape()
{
	const float Radius = GetRadius();
	const float Height = FMath::Max(GetHeight(), 1.f);
	Mound->SetRelativeLocation(FVector(0.f, 0.f, Height * 0.5f));
	Mound->SetRelativeScale3D(FVector(Radius / 50.f, Radius / 50.f, Height / 100.f));

	if (!MoundMID)
	{
		if (UMaterialInterface* Mat = Mound->GetMaterial(0))
		{
			MoundMID = Mound->CreateDynamicMaterialInstance(0, Mat);
		}
	}
	if (MoundMID)
	{
		MoundMID->SetVectorParameterValue(TEXT("Color"), Color);
	}
}

ADigSite* ADigSite::FindAt(UWorld* World, const FVector& WorldPoint)
{
	if (!World)
	{
		return nullptr;
	}
	for (TActorIterator<ADigSite> It(World); It; ++It)
	{
		if (!It->IsActorBeingDestroyed() && It->ContainsPoint(WorldPoint))
		{
			return *It;
		}
	}
	return nullptr;
}

void ADigSite::SpillAt(UWorld* World, const FVector& GroundPoint, const FDirtLoad& Load)
{
	if (!World || Load.IsEmpty() || World->GetNetMode() == NM_Client)
	{
		return;
	}

	// najblizsia kopa, na ktoru hlina dopadne
	ADigSite* Best = nullptr;
	double BestDist = TNumericLimits<double>::Max();
	for (TActorIterator<ADigSite> It(World); It; ++It)
	{
		if (It->IsActorBeingDestroyed())
		{
			continue;
		}
		const double Dist = FVector::Dist2D(It->GetActorLocation(), GroundPoint);
		const bool bClose = Dist <= It->GetRadius() + 50.f
			&& FMath::Abs(GroundPoint.Z - It->GetActorLocation().Z) <= It->GetHeight() + 200.f;
		if (bClose && Dist < BestDist)
		{
			BestDist = Dist;
			Best = *It;
		}
	}
	if (Best)
	{
		Best->AddLoad(Load);
		return;
	}

	const FTransform Transform(GroundPoint);
	ADigSite* Site = World->SpawnActorDeferred<ADigSite>(ADigSite::StaticClass(), Transform, nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
	if (Site)
	{
		Site->InitialDirt = Load.Dirt;
		Site->GoldPerTon = Load.Gold / Load.Dirt;
		Site->Color = Load.Gold > 0.f ? MiningColors::Dirt : MiningColors::Waste;
		Site->FinishSpawning(Transform);
	}
}

void ADigSite::PourAt(UWorld* World, const FVector& From, const FDirtLoad& Load, const AActor* IgnoreActor)
{
	if (!World || Load.IsEmpty() || World->GetNetMode() == NM_Client)
	{
		return;
	}
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MiningPour), false, IgnoreActor);
	FDirtLoad Rest = Load;
	for (int32 i = 0; i < 6 && !Rest.IsEmpty(); ++i)
	{
		FHitResult Hit;
		if (!World->LineTraceSingleByChannel(Hit, From, From - FVector(0.f, 0.f, 3000.f), ECC_Visibility, Params))
		{
			return; // pod nami nic nie je
		}
		AActor* HitActor = Hit.GetActor();
		UDirtContainerComponent* Container = HitActor ? HitActor->FindComponentByClass<UDirtContainerComponent>() : nullptr;
		if (Container && Container->AcceptsPoint(Hit.ImpactPoint))
		{
			// do korby / nasypky; co sa nezmesti, pada dalej
			Rest = Container->AddLoad(Rest);
			Params.AddIgnoredActor(HitActor);
			continue;
		}
		if (HitActor && HitActor->IsA<APawn>())
		{
			Params.AddIgnoredActor(HitActor); // na stroj ani hraca sa kopa nesype
			continue;
		}
		SpillAt(World, Hit.ImpactPoint, Rest);
		return;
	}
}
