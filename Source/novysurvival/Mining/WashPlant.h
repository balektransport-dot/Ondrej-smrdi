// Triedicka: hlinu vysypanu do nasypky po kuskoch preplachne v bubne, zlato odlozi
// a odpad vysype na kopu za strojom.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MiningTypes.h"
#include "WashPlant.generated.h"

class UDirtContainerComponent;
class UStaticMeshComponent;
class UTextRenderComponent;

UCLASS()
class NOVYSURVIVAL_API AWashPlant : public AActor
{
	GENERATED_BODY()

public:
	AWashPlant();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	// Kolko ton hliny spracuje za sekundu.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float ProcessRate = 0.6f;

	UFUNCTION(BlueprintPure, Category = "Mining")
	float GetTotalGold() const { return TotalGold; }

	UFUNCTION(BlueprintPure, Category = "Mining")
	UDirtContainerComponent* GetHopper() const { return Hopper; }

protected:
	void UpdateVisuals(float DeltaTime);

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UDirtContainerComponent> Hopper;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> Trommel;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> WasteOutlet;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UStaticMeshComponent> GoldPile;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UTextRenderComponent> Label;

	UPROPERTY()
	FLowPolyParts Visual;

	// Zlato v gramoch.
	UPROPERTY(Replicated)
	float TotalGold = 0.f;

	UPROPERTY(Replicated)
	bool bRunning = false;

	float WasteBuffer = 0.f;
};
