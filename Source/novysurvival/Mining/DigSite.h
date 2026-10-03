// Kopa hliny (lozisko so zlatom alebo vysypana kopa). Tvar kuzela – cim menej hliny, tym mensia.
// Lozisko poloz do levelu na zem; vysypane kopy vznikaju samy.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MiningTypes.h"
#include "DigSite.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;

UCLASS()
class NOVYSURVIVAL_API ADigSite : public AActor
{
	GENERATED_BODY()

public:
	ADigSite();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	// Vykope najviac Amount ton.
	FDirtLoad Dig(float Amount);

	void AddLoad(const FDirtLoad& Load);

	// Je bod (napr. spicka lopaty) v kope?
	bool ContainsPoint(const FVector& WorldPoint, float Tolerance = 30.f) const;

	float GetRadius() const;
	float GetHeight() const;

	UFUNCTION(BlueprintPure, Category = "Mining")
	float GetDirt() const { return Dirt; }

	// Kopa, v ktorej je bod (alebo nullptr).
	static ADigSite* FindAt(UWorld* World, const FVector& WorldPoint);

	// Vysype hlinu na zem v bode: prida do kopy, ktora tam je, alebo vytvori novu.
	static void SpillAt(UWorld* World, const FVector& GroundPoint, const FDirtLoad& Load);

	// Sype hlinu z bodu nadol: do nadoby pod nim (korba, nasypka), co sa nezmesti, padne na zem.
	static void PourAt(UWorld* World, const FVector& From, const FDirtLoad& Load, const AActor* IgnoreActor);

	// Kolko ton hliny je v kope na zaciatku.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining", meta = (ClampMin = "0.1"))
	float InitialDirt = 60.f;

	// Kolko gramov zlata je v tone hliny.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining", meta = (ClampMin = "0"))
	float GoldPerTon = 2.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Mining")
	FLinearColor Color = MiningColors::Dirt;

protected:
	UFUNCTION()
	void OnRep_Dirt();

	void UpdateShape();

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UStaticMeshComponent> Mound;

	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> MoundMID;

	UPROPERTY(ReplicatedUsing = OnRep_Dirt)
	float Dirt = 0.f;

	float Gold = 0.f;
	bool bInitialized = false;
};
