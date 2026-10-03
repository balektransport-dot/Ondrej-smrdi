// Nadoba na hlinu: lopata bagra, korba sklapaca, nasypka triedicky.
// Komponent stoji na dne nadoby, FillSize je velkost plnej kopy hliny v nej.
#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "MiningTypes.h"
#include "DirtContainerComponent.generated.h"

class UStaticMeshComponent;

UCLASS(ClassGroup = (Mining), meta = (BlueprintSpawnableComponent))
class NOVYSURVIVAL_API UDirtContainerComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	UDirtContainerComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;

	// Prida hlinu, vrati to, co sa uz nezmestilo.
	FDirtLoad AddLoad(const FDirtLoad& Load);

	// Vyberie najviac Amount ton (zlato v pomere).
	FDirtLoad TakeLoad(float Amount);

	// Je bod nad touto nadobou (napr. lopata nad korbou)?
	bool AcceptsPoint(const FVector& WorldPoint) const;

	UFUNCTION(BlueprintPure, Category = "Mining")
	float GetDirt() const { return Dirt; }

	UFUNCTION(BlueprintPure, Category = "Mining")
	float GetGold() const { return Gold; }

	UFUNCTION(BlueprintPure, Category = "Mining")
	float GetFreeSpace() const { return FMath::Max(0.f, Capacity - Dirt); }

	UFUNCTION(BlueprintPure, Category = "Mining")
	bool IsFull() const { return Dirt >= Capacity - 0.001f; }

	UFUNCTION(BlueprintPure, Category = "Mining")
	bool IsEmpty() const { return Dirt <= 0.001f; }

	// Kapacita v tonach.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float Capacity = 1.f;

	// Rozmer plnej kopy (cm).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	FVector FillSize = FVector(100.f);

	// Kocka, ktora ukazuje, kolko hliny je vnutri (nastavi vlastnik).
	UPROPERTY(EditAnywhere, Category = "Mining")
	TObjectPtr<UStaticMeshComponent> FillVisual;

protected:
	UFUNCTION()
	void OnRep_Load();

	void UpdateVisual();

	UPROPERTY(ReplicatedUsing = OnRep_Load)
	float Dirt = 0.f;

	UPROPERTY(Replicated)
	float Gold = 0.f;
};
