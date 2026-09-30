// Jeden polozeny stavebny diel (zaklad, stena, dvere...) alebo polozeny predmet.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BuildTypes.h"
#include "BuildPiece.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;

UCLASS()
class NOVYSURVIVAL_API ABuildPiece : public AActor
{
	GENERATED_BODY()

public:
	ABuildPiece();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	// Volat pred FinishSpawning.
	void InitPiece(const FBuildRequest& Req, EBuildTier InTier, float InMaxHealth, UStaticMesh* InPropMesh);

	// Nahlad (hologram) – bez kolizie, bez registracie v mriezke.
	void SetupPreview(EBuildPieceType InType, UStaticMesh* InPropMesh, UMaterialInterface* GhostMaterial);
	void SetPreviewValid(bool bValid);

	void SetTier(EBuildTier NewTier, float NewMaxHealth);
	void ToggleDoor();

	UFUNCTION(BlueprintPure, Category = "Building")
	FText GetTierName() const;

	UPROPERTY(ReplicatedUsing = OnRep_Visual, BlueprintReadOnly, Category = "Building")
	EBuildPieceType PieceType = EBuildPieceType::Wall;

	UPROPERTY(ReplicatedUsing = OnRep_Visual, BlueprintReadOnly, Category = "Building")
	EBuildTier Tier = EBuildTier::Wood;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	float Health = 100.f;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	float MaxHealth = 100.f;

	UPROPERTY(ReplicatedUsing = OnRep_Door, BlueprintReadOnly, Category = "Building")
	bool bDoorOpen = false;

	// Mriezka budovy (rovnaka pre vsetky diely jednej stavby).
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	FVector GridOrigin = FVector::ZeroVector;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	float GridYaw = 0.f;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	FIntVector Cell = FIntVector::ZeroValue;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	EBuildSlot Slot = EBuildSlot::None;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	int32 RoofDir = 0;

	// Pre Prop: ID predmetu v inventari (vrati sa pri zburani).
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Building")
	FName ItemID;

	UPROPERTY(ReplicatedUsing = OnRep_Visual, BlueprintReadOnly, Category = "Building")
	TObjectPtr<UStaticMesh> PropMesh;

	// Farby materialov (drevo, kamen, kov).
	UPROPERTY(EditDefaultsOnly, Category = "Building")
	TArray<FLinearColor> TierColors;

	bool IsPreview() const { return bPreview; }
	bool IsInGrid() const { return !bPreview && Slot != EBuildSlot::None; }

protected:
	UFUNCTION()
	void OnRep_Visual();

	UFUNCTION()
	void OnRep_Door();

	void RebuildVisual();
	void ApplyMaterials();

	UPROPERTY(VisibleAnywhere, Category = "Building")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "Building")
	TObjectPtr<USceneComponent> Hinge;

	UPROPERTY(VisibleAnywhere, Category = "Building")
	TArray<TObjectPtr<UStaticMeshComponent>> Parts;

	UPROPERTY()
	TObjectPtr<UStaticMesh> CubeMesh;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> BaseMaterial;

	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> TierMID;

	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> GhostMID;

	bool bPreview = false;
	bool bRegistered = false;
};
