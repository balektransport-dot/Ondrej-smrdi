#include "WashPlant.h"
#include "DigSite.h"
#include "DirtContainerComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Net/UnrealNetwork.h"

AWashPlant::AWashPlant()
{
	PrimaryActorTick.bCanEverTick = true;
	bReplicates = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	using namespace MiningColors;
	const ELowPolyShape Box = ELowPolyShape::Cube;

	// nasypka pri zemi – sklapac do nej cuva, bager do nej sype
	Visual.Add(this, TEXT("HopperFloor"), Root, Box, FVector(0.f, 0.f, 15.f), FVector(420.f, 420.f, 30.f), Steel);
	Visual.Add(this, TEXT("HopperWallL"), Root, Box, FVector(0.f, -210.f, 55.f), FVector(420.f, 15.f, 80.f), Green);
	Visual.Add(this, TEXT("HopperWallR"), Root, Box, FVector(0.f, 210.f, 55.f), FVector(420.f, 15.f, 80.f), Green);
	Visual.Add(this, TEXT("HopperWallBack"), Root, Box, FVector(210.f, 0.f, 55.f), FVector(15.f, 420.f, 80.f), Green);

	Hopper = CreateDefaultSubobject<UDirtContainerComponent>(TEXT("Hopper"));
	Hopper->SetupAttachment(Root);
	Hopper->SetRelativeLocation(FVector(0.f, 0.f, 30.f));
	Hopper->Capacity = 20.f;
	Hopper->FillSize = FVector(390.f, 390.f, 60.f);
	Hopper->FillVisual = Visual.Add(this, TEXT("HopperDirt"), Hopper, Box, FVector::ZeroVector, FVector(100.f), MiningColors::Dirt);

	// pas hore do bubna
	Visual.Add(this, TEXT("Conveyor"), Root, Box, FVector(440.f, 0.f, 170.f), FVector(500.f, 80.f, 20.f), Dark, FRotator(25.f, 0.f, 0.f));

	// bubon (triedenie), toci sa, ked stroj pracuje
	Trommel = CreateDefaultSubobject<USceneComponent>(TEXT("Trommel"));
	Trommel->SetupAttachment(Root);
	Trommel->SetRelativeLocation(FVector(900.f, 0.f, 330.f));
	Visual.Add(this, TEXT("Drum"), Trommel, ELowPolyShape::Cylinder, FVector::ZeroVector, FVector(220.f, 220.f, 500.f), Steel, FRotator(90.f, 0.f, 0.f));
	Visual.Add(this, TEXT("DrumStripe"), Trommel, Box, FVector(0.f, 0.f, 112.f), FVector(480.f, 30.f, 10.f), Yellow);

	Visual.Add(this, TEXT("LegFL"), Root, Box, FVector(720.f, -100.f, 110.f), FVector(20.f, 20.f, 220.f), Dark);
	Visual.Add(this, TEXT("LegFR"), Root, Box, FVector(720.f, 100.f, 110.f), FVector(20.f, 20.f, 220.f), Dark);
	Visual.Add(this, TEXT("LegBL"), Root, Box, FVector(1080.f, -100.f, 110.f), FVector(20.f, 20.f, 220.f), Dark);
	Visual.Add(this, TEXT("LegBR"), Root, Box, FVector(1080.f, 100.f, 110.f), FVector(20.f, 20.f, 220.f), Dark);

	// stol so zlatom
	Visual.Add(this, TEXT("GoldTable"), Root, Box, FVector(900.f, -280.f, 45.f), FVector(160.f, 120.f, 90.f), Yellow);
	GoldPile = Visual.Add(this, TEXT("GoldPile"), Root, ELowPolyShape::Sphere, FVector(900.f, -280.f, 95.f), FVector(1.f), Gold);
	GoldPile->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	// odpad sa sype za bubon
	WasteOutlet = CreateDefaultSubobject<USceneComponent>(TEXT("WasteOutlet"));
	WasteOutlet->SetupAttachment(Root);
	WasteOutlet->SetRelativeLocation(FVector(1350.f, 0.f, 300.f));

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Root);
	Label->SetRelativeLocation(FVector(-220.f, 0.f, 320.f));
	Label->SetRelativeRotation(FRotator(0.f, 180.f, 0.f)); // citatelne od nasypky
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(45.f);
	Label->SetTextRenderColor(FColor(255, 200, 40));
}

void AWashPlant::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AWashPlant, TotalGold);
	DOREPLIFETIME(AWashPlant, bRunning);
}

void AWashPlant::BeginPlay()
{
	Super::BeginPlay();
	Visual.ApplyColors(this);
	UpdateVisuals(0.f);
}

void AWashPlant::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (HasAuthority())
	{
		bRunning = !Hopper->IsEmpty();
		if (bRunning)
		{
			// zlato zostane, hlina ide do odpadu
			const FDirtLoad Load = Hopper->TakeLoad(ProcessRate * DeltaTime);
			TotalGold += Load.Gold;
			WasteBuffer += Load.Dirt;
		}
		if (WasteBuffer >= 0.25f || (!bRunning && WasteBuffer > 0.f))
		{
			ADigSite::PourAt(GetWorld(), WasteOutlet->GetComponentLocation(), FDirtLoad(WasteBuffer, 0.f), this);
			WasteBuffer = 0.f;
		}
	}

	UpdateVisuals(DeltaTime);
}

void AWashPlant::UpdateVisuals(float DeltaTime)
{
	if (bRunning)
	{
		Trommel->AddLocalRotation(FRotator(0.f, 0.f, 90.f * DeltaTime));
	}

	// kopka zlata rastie (objem ~ gramy)
	const float Size = TotalGold > 0.f ? 8.f + 10.f * FMath::Pow(TotalGold, 1.f / 3.f) : 1.f;
	GoldPile->SetVisibility(TotalGold > 0.f);
	GoldPile->SetRelativeScale3D(FVector(Size, Size, Size * 0.6f) / 100.f);

	Label->SetText(FText::FromString(FString::Printf(TEXT("TRIEDICKA\nZlato: %.2f g\nNasypka: %.1f / %.0f t"),
		TotalGold, Hopper->GetDirt(), Hopper->Capacity)));
}
