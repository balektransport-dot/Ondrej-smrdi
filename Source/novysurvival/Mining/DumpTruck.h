// Sklapac: odvezie hlinu od bagra k triedicke. Medzernik vyklopi korbu, hlina sa vysype vzadu.
#pragma once

#include "CoreMinimal.h"
#include "MiningVehicle.h"
#include "DumpTruck.generated.h"

class UDirtContainerComponent;

UCLASS()
class NOVYSURVIVAL_API ADumpTruck : public AMiningVehicle
{
	GENERATED_BODY()

public:
	ADumpTruck();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintPure, Category = "Mining")
	UDirtContainerComponent* GetBed() const { return Bed; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Bed")
	float BedRate = 20.f; // stupne/s

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Bed")
	float MaxBedAngle = 50.f;

	// Kolko ton/s sa vysype pri plne vyklopenej korbe.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Bed")
	float DumpRate = 4.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Bed")
	FKey DumpKey = EKeys::SpaceBar;

protected:
	virtual void UpdateControls(APlayerController* PC, float DeltaTime) override;
	virtual FString GetStatusText() const override;

	UFUNCTION()
	void OnRep_BedAngle();

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> BedPivot;

	// Odtial sa hlina sype (za korbou).
	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> BedOutlet;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UDirtContainerComponent> Bed;

	UPROPERTY(ReplicatedUsing = OnRep_BedAngle)
	float BedAngle = 0.f;
};
