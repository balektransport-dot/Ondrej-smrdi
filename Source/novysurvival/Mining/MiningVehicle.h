// Spolocny zaklad strojov (bager, sklapac): jazda po terene, kamera, nastupovanie klavesom F.
// Klavesy sa citaju priamo (netreba nastavovat Input Actions).
// Zatial pre singleplayer / hraca na serveri.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "InputCoreTypes.h"
#include "MiningTypes.h"
#include "MiningVehicle.generated.h"

class UBoxComponent;
class USpringArmComponent;
class UCameraComponent;
class APlayerController;

UCLASS(Abstract)
class NOVYSURVIVAL_API AMiningVehicle : public APawn
{
	GENERATED_BODY()

public:
	AMiningVehicle();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UFUNCTION(BlueprintCallable, Category = "Mining")
	bool EnterVehicle(APawn* NewDriver);

	UFUNCTION(BlueprintCallable, Category = "Mining")
	void ExitVehicle();

	UFUNCTION(BlueprintPure, Category = "Mining")
	APawn* GetDriver() const { return Driver; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Drive")
	float MaxSpeed = 700.f; // cm/s

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Drive")
	float Acceleration = 350.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Drive")
	float TurnRate = 45.f; // stupne/s

	// Pasy sa vedia otacat na mieste, kolesa len za jazdy.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Drive")
	bool bTurnInPlace = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float EnterDistance = 450.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	FKey EnterKey = EKeys::F;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	FText VehicleName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float MouseSensitivity = 2.5f;

protected:
	// Potomok: vlastne ovladanie (vola sa kazdy tick, ked stroj riadi hrac).
	virtual void UpdateControls(APlayerController* PC, float DeltaTime) {}

	// Potomok: text do rohu obrazovky (naklad, ovladanie...).
	virtual FString GetStatusText() const { return FString(); }

	// +1 ked je stlaceny Plus, -1 ked Minus.
	static float KeyAxis(const APlayerController* PC, const FKey& Plus, const FKey& Minus);

	// Vyska stredu tela nad zemou (cm). Diely potomkov maju zem na Z = -GroundOffset.
	float GetGroundOffset() const;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UBoxComponent> Body;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USpringArmComponent> CameraArm;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY()
	FLowPolyParts Visual;

	// Medzera medzi spodkom tela a zemou (cm).
	float GroundClearance = 40.f;

private:
	void Drive(float Throttle, float Steer, float DeltaTime);
	void CheckEnter();

	UPROPERTY()
	TObjectPtr<APawn> Driver;

	float Speed = 0.f;
	uint64 EnterFrame = 0;
};
