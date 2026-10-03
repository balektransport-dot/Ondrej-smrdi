#include "DumpTruck.h"
#include "DigSite.h"
#include "DirtContainerComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Net/UnrealNetwork.h"

ADumpTruck::ADumpTruck()
{
	VehicleName = NSLOCTEXT("Mining", "DumpTruck", "Sklápač");
	bTurnInPlace = false;
	MaxSpeed = 1000.f;
	TurnRate = 50.f;
	GroundClearance = 50.f;
	Body->SetBoxExtent(FVector(260.f, 120.f, 50.f));
	CameraArm->TargetArmLength = 1000.f;
	CameraArm->SocketOffset = FVector(0.f, 0.f, 300.f);

	using namespace MiningColors;
	const ELowPolyShape Box = ELowPolyShape::Cube;
	const ELowPolyShape Cyl = ELowPolyShape::Cylinder;
	const FRotator Axle(0.f, 0.f, 90.f);
	const float WheelZ = -100.f + 55.f; // zem je 100 cm pod stredom tela
	const FVector WheelSize(110.f, 110.f, 50.f);

	Visual.Add(this, TEXT("Chassis"), Body, Box, FVector(0.f, 0.f, -10.f), FVector(520.f, 200.f, 40.f), Dark);
	Visual.Add(this, TEXT("WheelFL"), Body, Cyl, FVector(170.f, -125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("WheelFR"), Body, Cyl, FVector(170.f, 125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("WheelML"), Body, Cyl, FVector(-90.f, -125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("WheelMR"), Body, Cyl, FVector(-90.f, 125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("WheelBL"), Body, Cyl, FVector(-205.f, -125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("WheelBR"), Body, Cyl, FVector(-205.f, 125.f, WheelZ), WheelSize, Dark, Axle);
	Visual.Add(this, TEXT("Cab"), Body, Box, FVector(195.f, 0.f, 95.f), FVector(130.f, 220.f, 170.f), Orange);
	Visual.Add(this, TEXT("Window"), Body, Box, FVector(261.f, 0.f, 130.f), FVector(8.f, 190.f, 70.f), Glass);
	Visual.Add(this, TEXT("Bumper"), Body, Box, FVector(265.f, 0.f, -20.f), FVector(20.f, 230.f, 30.f), Steel);

	// korba sa klopi okolo zadneho pantu
	BedPivot = CreateDefaultSubobject<USceneComponent>(TEXT("BedPivot"));
	BedPivot->SetupAttachment(Body);
	BedPivot->SetRelativeLocation(FVector(-260.f, 0.f, 20.f));
	Visual.Add(this, TEXT("BedFloor"), BedPivot, Box, FVector(200.f, 0.f, 8.f), FVector(400.f, 230.f, 15.f), Orange);
	Visual.Add(this, TEXT("BedFront"), BedPivot, Box, FVector(400.f, 0.f, 70.f), FVector(15.f, 230.f, 120.f), Orange);
	Visual.Add(this, TEXT("BedSideL"), BedPivot, Box, FVector(200.f, -115.f, 65.f), FVector(400.f, 12.f, 110.f), Orange);
	Visual.Add(this, TEXT("BedSideR"), BedPivot, Box, FVector(200.f, 115.f, 65.f), FVector(400.f, 12.f, 110.f), Orange);

	BedOutlet = CreateDefaultSubobject<USceneComponent>(TEXT("BedOutlet"));
	BedOutlet->SetupAttachment(BedPivot);
	BedOutlet->SetRelativeLocation(FVector(-40.f, 0.f, 30.f));

	Bed = CreateDefaultSubobject<UDirtContainerComponent>(TEXT("Bed"));
	Bed->SetupAttachment(BedPivot);
	Bed->SetRelativeLocation(FVector(200.f, 0.f, 15.f));
	Bed->Capacity = 12.f;
	Bed->FillSize = FVector(380.f, 210.f, 100.f);
	Bed->FillVisual = Visual.Add(this, TEXT("BedDirt"), Bed, Box, FVector::ZeroVector, FVector(100.f), MiningColors::Dirt);
}

void ADumpTruck::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ADumpTruck, BedAngle);
}

void ADumpTruck::BeginPlay()
{
	Super::BeginPlay();
	OnRep_BedAngle();
}

void ADumpTruck::UpdateControls(APlayerController* PC, float DeltaTime)
{
	const float Dir = PC->IsInputKeyDown(DumpKey) ? 1.f : -1.f;
	BedAngle = FMath::Clamp(BedAngle + Dir * BedRate * DeltaTime, 0.f, MaxBedAngle);
	OnRep_BedAngle();

	// od 20 stupnov sa hlina zacne sypat, cim viac vyklopene, tym rychlejsie
	const float Tilt = (float)FMath::GetMappedRangeValueClamped(FVector2D(20.f, MaxBedAngle), FVector2D(0.f, 1.f), BedAngle);
	if (Tilt > 0.f && !Bed->IsEmpty())
	{
		ADigSite::PourAt(GetWorld(), BedOutlet->GetComponentLocation(), Bed->TakeLoad(DumpRate * Tilt * DeltaTime), this);
	}
}

void ADumpTruck::OnRep_BedAngle()
{
	BedPivot->SetRelativeRotation(FRotator(BedAngle, 0.f, 0.f));
}

FString ADumpTruck::GetStatusText() const
{
	return FString::Printf(TEXT("Korba: %.1f / %.0f t  (zlato v nej %.1f g)\nDrž medzerník = vyklopiť korbu (vysype sa vzadu)"),
		Bed->GetDirt(), Bed->Capacity, Bed->GetGold());
}
