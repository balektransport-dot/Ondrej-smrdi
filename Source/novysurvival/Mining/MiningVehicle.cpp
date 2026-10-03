#include "MiningVehicle.h"
#include "CoreGlobals.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PawnMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"

AMiningVehicle::AMiningVehicle()
{
	PrimaryActorTick.bCanEverTick = true;
	bReplicates = true;
	SetReplicateMovement(true);
	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;
	AutoPossessPlayer = EAutoReceiveInput::Disabled;

	// Telo na kolizie; je trochu nad zemou, aby sa nezasekavalo o teren.
	Body = CreateDefaultSubobject<UBoxComponent>(TEXT("Body"));
	Body->SetBoxExtent(FVector(200.f, 120.f, 50.f));
	Body->SetCollisionProfileName(TEXT("Vehicle"));
	RootComponent = Body;

	CameraArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraArm"));
	CameraArm->SetupAttachment(Body);
	CameraArm->TargetArmLength = 900.f;
	CameraArm->SocketOffset = FVector(0.f, 0.f, 250.f);
	CameraArm->bUsePawnControlRotation = true;
	CameraArm->bEnableCameraLag = true;
	CameraArm->CameraLagSpeed = 8.f;

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(CameraArm, USpringArmComponent::SocketName);

	VehicleName = NSLOCTEXT("Mining", "Vehicle", "Stroj");
}

void AMiningVehicle::BeginPlay()
{
	Super::BeginPlay();
	Visual.ApplyColors(this);
}

float AMiningVehicle::KeyAxis(const APlayerController* PC, const FKey& Plus, const FKey& Minus)
{
	return (PC->IsInputKeyDown(Plus) ? 1.f : 0.f) - (PC->IsInputKeyDown(Minus) ? 1.f : 0.f);
}

float AMiningVehicle::GetGroundOffset() const
{
	return Body->GetUnscaledBoxExtent().Z + GroundClearance;
}

void AMiningVehicle::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (!HasAuthority())
	{
		return;
	}

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC || !PC->IsLocalController())
	{
		Drive(0.f, 0.f, DeltaTime); // dobrzdi a sadne na zem
		CheckEnter();
		return;
	}

	// mys otaca kameru
	float MouseX = 0.f;
	float MouseY = 0.f;
	PC->GetInputMouseDelta(MouseX, MouseY);
	FRotator View = PC->GetControlRotation();
	View.Yaw += MouseX * MouseSensitivity;
	View.Pitch = FMath::Clamp(FRotator::NormalizeAxis(View.Pitch + MouseY * MouseSensitivity), -70.f, 30.f);
	PC->SetControlRotation(View);

	Drive(KeyAxis(PC, EKeys::W, EKeys::S), KeyAxis(PC, EKeys::D, EKeys::A), DeltaTime);
	UpdateControls(PC, DeltaTime);

	if (GEngine)
	{
		const FString Text = FString::Printf(TEXT("%s  |  W/S jazda, A/D zatáčanie, myš kamera, F vystúpiť\n%s"),
			*VehicleName.ToString(), *GetStatusText());
		GEngine->AddOnScreenDebugMessage((uint64)GetUniqueID(), 0.f, FColor::Yellow, Text);
	}

	if (PC->WasInputKeyJustPressed(EnterKey) && GFrameCounter != EnterFrame)
	{
		ExitVehicle();
	}
}

void AMiningVehicle::Drive(float Throttle, float Steer, float DeltaTime)
{
	const float Rate = FMath::IsNearlyZero(Throttle) ? Acceleration * 1.5f : Acceleration;
	Speed = FMath::FInterpConstantTo(Speed, Throttle * MaxSpeed, DeltaTime, Rate);

	FRotator Rot = GetActorRotation();
	// kolesa zatacaju len za jazdy (a pri cuvani naopak), pasy aj na mieste
	const float TurnFactor = bTurnInPlace ? 1.f : FMath::Clamp(Speed / (MaxSpeed * 0.3f), -1.f, 1.f);
	Rot.Yaw += Steer * TurnRate * TurnFactor * DeltaTime;

	const FVector Forward = FRotator(0.f, Rot.Yaw, 0.f).Vector();
	FVector NewLoc = GetActorLocation() + Forward * Speed * DeltaTime;

	// drz sa zeme a naklon sa podla svahu
	FCollisionQueryParams Params(SCENE_QUERY_STAT(MiningVehicleGround), false, this);
	if (Driver)
	{
		Params.AddIgnoredActor(Driver);
	}
	FHitResult Ground;
	if (GetWorld()->LineTraceSingleByChannel(Ground, NewLoc + FVector(0.f, 0.f, 100.f), NewLoc - FVector(0.f, 0.f, 3000.f), ECC_Visibility, Params))
	{
		const double Dt = DeltaTime;
		const double TargetZ = Ground.ImpactPoint.Z + GetGroundOffset();
		NewLoc.Z = TargetZ > NewLoc.Z
			? FMath::FInterpTo(NewLoc.Z, TargetZ, Dt, 12.0)
			: FMath::FInterpConstantTo(NewLoc.Z, TargetZ, Dt, 980.0); // padanie
		const FRotator Tilt = FRotationMatrix::MakeFromZX(FVector(Ground.ImpactNormal), Forward).Rotator();
		Rot.Pitch = FMath::FInterpTo(Rot.Pitch, Tilt.Pitch, Dt, 5.0);
		Rot.Roll = FMath::FInterpTo(Rot.Roll, Tilt.Roll, Dt, 5.0);
	}

	FHitResult Hit;
	SetActorLocationAndRotation(NewLoc, Rot, true, &Hit);
	if (Hit.bBlockingHit)
	{
		Speed = 0.f; // naraz
	}
}

void AMiningVehicle::CheckEnter()
{
	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	APawn* Walker = PC ? PC->GetPawn() : nullptr;
	if (!PC || !PC->IsLocalController() || !Walker || Walker->IsA<AMiningVehicle>())
	{
		return;
	}
	if (FVector::Dist(Walker->GetActorLocation(), GetActorLocation()) > EnterDistance)
	{
		return;
	}
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage((uint64)GetUniqueID(), 0.f, FColor::White,
			FString::Printf(TEXT("F = nastúpiť: %s"), *VehicleName.ToString()));
	}
	if (PC->WasInputKeyJustPressed(EnterKey))
	{
		EnterVehicle(Walker);
	}
}

bool AMiningVehicle::EnterVehicle(APawn* NewDriver)
{
	if (!HasAuthority() || !NewDriver || Driver || GetController())
	{
		return false;
	}
	APlayerController* PC = Cast<APlayerController>(NewDriver->GetController());
	if (!PC)
	{
		return false;
	}

	Driver = NewDriver;
	EnterFrame = GFrameCounter;

	// postava sa schova do kabiny a vezie sa so strojom
	if (UPawnMovementComponent* Move = Driver->GetMovementComponent())
	{
		Move->StopMovementImmediately();
		Move->Deactivate();
	}
	Driver->SetActorEnableCollision(false);
	Driver->SetActorHiddenInGame(true);
	Driver->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);

	PC->Possess(this);
	return true;
}

void AMiningVehicle::ExitVehicle()
{
	if (!HasAuthority() || !Driver)
	{
		return;
	}
	APlayerController* PC = Cast<APlayerController>(GetController());
	APawn* Pawn = Driver;
	Driver = nullptr;
	Speed = 0.f;

	Pawn->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
	Pawn->SetActorEnableCollision(true);
	Pawn->SetActorHiddenInGame(false);

	// vystup vlavo, ak tam nie je miesto, tak vpravo, inak navrch
	const FRotator ExitRot(0.f, GetActorRotation().Yaw, 0.f);
	const FVector Side = GetActorRightVector() * (Body->GetScaledBoxExtent().Y + 150.f);
	const FVector Up(0.f, 0.f, 60.f);
	if (!Pawn->TeleportTo(GetActorLocation() - Side + Up, ExitRot)
		&& !Pawn->TeleportTo(GetActorLocation() + Side + Up, ExitRot))
	{
		Pawn->TeleportTo(GetActorLocation() + FVector(0.f, 0.f, Body->GetScaledBoxExtent().Z + 250.f), ExitRot);
	}

	if (UPawnMovementComponent* Move = Pawn->GetMovementComponent())
	{
		Move->Activate(true);
	}
	if (ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		Character->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
	}

	if (PC)
	{
		PC->Possess(Pawn);
	}
}
