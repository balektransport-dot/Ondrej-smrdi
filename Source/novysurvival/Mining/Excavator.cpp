#include "Excavator.h"
#include "DigSite.h"
#include "DirtContainerComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Net/UnrealNetwork.h"

namespace
{
	constexpr float BucketOpenPitch = -60.f;  // lopata otvorena – sype
	constexpr float BucketClosedPitch = 80.f; // lopata zatvorena – drzi
	constexpr float DumpCurl = 0.15f;         // pod tymto sa hlina sype von
}

AExcavator::AExcavator()
{
	VehicleName = NSLOCTEXT("Mining", "Excavator", "Bager");
	bTurnInPlace = true;
	MaxSpeed = 350.f;
	TurnRate = 35.f;
	Body->SetBoxExtent(FVector(220.f, 140.f, 45.f));
	CameraArm->TargetArmLength = 1200.f;
	CameraArm->SocketOffset = FVector(0.f, 0.f, 350.f);

	using namespace MiningColors;
	const ELowPolyShape Box = ELowPolyShape::Cube;
	const ELowPolyShape Cyl = ELowPolyShape::Cylinder;
	const FRotator Axle(0.f, 0.f, 90.f);
	const float G = -85.f; // zem pod telom (extent Z + svetla vyska)

	// podvozok s pasmi
	Visual.Add(this, TEXT("TrackL"), Body, Box, FVector(0.f, -115.f, G + 40.f), FVector(440.f, 70.f, 80.f), Dark);
	Visual.Add(this, TEXT("TrackR"), Body, Box, FVector(0.f, 115.f, G + 40.f), FVector(440.f, 70.f, 80.f), Dark);
	Visual.Add(this, TEXT("WheelFL"), Body, Cyl, FVector(205.f, -115.f, G + 40.f), FVector(85.f, 85.f, 74.f), Steel, Axle);
	Visual.Add(this, TEXT("WheelFR"), Body, Cyl, FVector(205.f, 115.f, G + 40.f), FVector(85.f, 85.f, 74.f), Steel, Axle);
	Visual.Add(this, TEXT("WheelBL"), Body, Cyl, FVector(-205.f, -115.f, G + 40.f), FVector(85.f, 85.f, 74.f), Steel, Axle);
	Visual.Add(this, TEXT("WheelBR"), Body, Cyl, FVector(-205.f, 115.f, G + 40.f), FVector(85.f, 85.f, 74.f), Steel, Axle);
	Visual.Add(this, TEXT("Undercarriage"), Body, Box, FVector(0.f, 0.f, -25.f), FVector(300.f, 160.f, 50.f), Steel);

	// otocna horna cast
	Upper = CreateDefaultSubobject<USceneComponent>(TEXT("Upper"));
	Upper->SetupAttachment(Body);
	Upper->SetRelativeLocation(FVector(0.f, 0.f, 20.f));
	Visual.Add(this, TEXT("Turntable"), Upper, Cyl, FVector(0.f, 0.f, 0.f), FVector(170.f, 170.f, 20.f), Dark);
	Visual.Add(this, TEXT("Deck"), Upper, Box, FVector(-30.f, 0.f, 45.f), FVector(330.f, 260.f, 70.f), Yellow);
	Visual.Add(this, TEXT("Counterweight"), Upper, Box, FVector(-180.f, 0.f, 65.f), FVector(90.f, 260.f, 110.f), Steel);
	Visual.Add(this, TEXT("Cab"), Upper, Box, FVector(60.f, -70.f, 165.f), FVector(150.f, 110.f, 170.f), Yellow);
	Visual.Add(this, TEXT("WindowFront"), Upper, Box, FVector(136.f, -70.f, 185.f), FVector(8.f, 96.f, 90.f), Glass);
	Visual.Add(this, TEXT("WindowSide"), Upper, Box, FVector(60.f, -126.f, 185.f), FVector(120.f, 8.f, 80.f), Glass);
	Visual.Add(this, TEXT("Hood"), Upper, Box, FVector(-95.f, 60.f, 102.f), FVector(150.f, 120.f, 45.f), Yellow);
	Visual.Add(this, TEXT("Exhaust"), Upper, Cyl, FVector(-60.f, 100.f, 150.f), FVector(12.f, 12.f, 60.f), Dark);

	// vyloznik -> rameno -> lopata
	BoomPivot = CreateDefaultSubobject<USceneComponent>(TEXT("BoomPivot"));
	BoomPivot->SetupAttachment(Upper);
	BoomPivot->SetRelativeLocation(FVector(110.f, 40.f, 90.f));
	Visual.Add(this, TEXT("Boom"), BoomPivot, Box, FVector(230.f, 0.f, 0.f), FVector(460.f, 45.f, 60.f), Yellow);

	StickPivot = CreateDefaultSubobject<USceneComponent>(TEXT("StickPivot"));
	StickPivot->SetupAttachment(BoomPivot);
	StickPivot->SetRelativeLocation(FVector(460.f, 0.f, 0.f));
	Visual.Add(this, TEXT("Stick"), StickPivot, Box, FVector(150.f, 0.f, 0.f), FVector(300.f, 40.f, 45.f), Yellow);

	BucketPivot = CreateDefaultSubobject<USceneComponent>(TEXT("BucketPivot"));
	BucketPivot->SetupAttachment(StickPivot);
	BucketPivot->SetRelativeLocation(FVector(295.f, 0.f, 0.f));
	// lopata = otvorena krabica, otvor smeruje na +Z
	Visual.Add(this, TEXT("BucketBack"), BucketPivot, Box, FVector(50.f, 0.f, 0.f), FVector(100.f, 110.f, 15.f), Steel);
	Visual.Add(this, TEXT("BucketLip"), BucketPivot, Box, FVector(100.f, 0.f, 35.f), FVector(15.f, 110.f, 70.f), Steel);
	Visual.Add(this, TEXT("BucketSideL"), BucketPivot, Box, FVector(52.f, -55.f, 30.f), FVector(100.f, 10.f, 60.f), Steel);
	Visual.Add(this, TEXT("BucketSideR"), BucketPivot, Box, FVector(52.f, 55.f, 30.f), FVector(100.f, 10.f, 60.f), Steel);

	BucketTip = CreateDefaultSubobject<USceneComponent>(TEXT("BucketTip"));
	BucketTip->SetupAttachment(BucketPivot);
	BucketTip->SetRelativeLocation(FVector(100.f, 0.f, 70.f));

	Bucket = CreateDefaultSubobject<UDirtContainerComponent>(TEXT("Bucket"));
	Bucket->SetupAttachment(BucketPivot);
	Bucket->SetRelativeLocation(FVector(50.f, 0.f, 8.f));
	Bucket->Capacity = 1.5f;
	Bucket->FillSize = FVector(85.f, 100.f, 55.f);
	Bucket->FillVisual = Visual.Add(this, TEXT("BucketDirt"), Bucket, Box, FVector::ZeroVector, FVector(100.f), MiningColors::Dirt);

	BucketCurl = 0.9f;
}

void AExcavator::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AExcavator, SwingYaw);
	DOREPLIFETIME(AExcavator, BoomPitch);
	DOREPLIFETIME(AExcavator, StickPitch);
	DOREPLIFETIME(AExcavator, BucketCurl);
}

void AExcavator::BeginPlay()
{
	Super::BeginPlay();
	ApplyArm();
}

void AExcavator::UpdateControls(APlayerController* PC, float DeltaTime)
{
	SwingYaw = (float)FRotator::NormalizeAxis(SwingYaw + KeyAxis(PC, EKeys::E, EKeys::Q) * SwingRate * DeltaTime);
	BoomPitch = FMath::Clamp(BoomPitch + KeyAxis(PC, EKeys::Up, EKeys::Down) * BoomRate * DeltaTime, -25.f, 55.f);
	StickPitch = FMath::Clamp(StickPitch + KeyAxis(PC, EKeys::Right, EKeys::Left) * StickRate * DeltaTime, -150.f, -35.f);
	UpdateBucket(KeyAxis(PC, EKeys::LeftMouseButton, EKeys::RightMouseButton), DeltaTime);
	ApplyArm();
}

void AExcavator::UpdateBucket(float Input, float DeltaTime)
{
	const float OldCurl = BucketCurl;
	BucketCurl = FMath::Clamp(BucketCurl + Input * BucketRate * DeltaTime, 0.f, 1.f);

	// naberanie: lopata sa zatvara a spicka je v kope
	if (BucketCurl > OldCurl && !Bucket->IsFull())
	{
		if (ADigSite* Site = ADigSite::FindAt(GetWorld(), BucketTip->GetComponentLocation()))
		{
			Bucket->AddLoad(Site->Dig(FMath::Min(DigRate * DeltaTime, Bucket->GetFreeSpace())));
		}
	}

	// vysypavanie: lopata je otvorena
	if (BucketCurl < DumpCurl && !Bucket->IsEmpty())
	{
		ADigSite::PourAt(GetWorld(), Bucket->GetComponentLocation(), Bucket->TakeLoad(DumpRate * DeltaTime), this);
	}
}

void AExcavator::OnRep_Arm()
{
	ApplyArm();
}

void AExcavator::ApplyArm()
{
	Upper->SetRelativeRotation(FRotator(0.f, SwingYaw, 0.f));
	BoomPivot->SetRelativeRotation(FRotator(BoomPitch, 0.f, 0.f));
	StickPivot->SetRelativeRotation(FRotator(StickPitch, 0.f, 0.f));
	BucketPivot->SetRelativeRotation(FRotator(FMath::Lerp(BucketOpenPitch, BucketClosedPitch, BucketCurl), 0.f, 0.f));
}

FString AExcavator::GetStatusText() const
{
	return FString::Printf(TEXT("Lopata: %.1f / %.1f t  (zlato v nej %.1f g)\n")
		TEXT("Q/E kabína | šípky hore/dole výložník | šípky vľavo/vpravo rameno | ľavé tlačidlo naberať | pravé vysypať"),
		Bucket->GetDirt(), Bucket->Capacity, Bucket->GetGold());
}
