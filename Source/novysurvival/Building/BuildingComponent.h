// Stavanie z pohladu hraca: nahlad (hologram), prichytenie k mriezke, polozenie,
// zburanie, vylepsenie materialu a otvaranie dveri.
// Pridaj na postavu hraca (alebo PlayerController) a vstupy napoj v Blueprinte na funkcie nizsie.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BuildTypes.h"
#include "BuildingComponent.generated.h"

class ABuildPiece;
class APawn;
class APlayerController;
class UMaterialInterface;
class UStaticMesh;
class UBuildingSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBuildMessage, const FText&, Message);

UCLASS(ClassGroup = (Building), meta = (BlueprintSpawnableComponent))
class NOVYSURVIVAL_API UBuildingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UBuildingComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	// --- Vstupy (volat z Blueprintu na lokalnom hracovi) ---

	UFUNCTION(BlueprintCallable, Category = "Building")
	void ToggleBuildMode();

	UFUNCTION(BlueprintCallable, Category = "Building")
	void SetBuildMode(bool bEnable);

	UFUNCTION(BlueprintCallable, Category = "Building")
	void SelectPiece(EBuildPieceType Type);

	// +1 = dalsi diel, -1 = predosly (napr. koliesko mysi).
	UFUNCTION(BlueprintCallable, Category = "Building")
	void SelectNextPiece(int32 Direction = 1);

	// Polozenie predmetu z inventara (ItemID musi byt v PropMeshes). Zapne rezim stavania.
	UFUNCTION(BlueprintCallable, Category = "Building")
	void SelectProp(FName ItemID);

	UFUNCTION(BlueprintCallable, Category = "Building")
	void RotatePreview();

	UFUNCTION(BlueprintCallable, Category = "Building")
	void TryPlace();

	UFUNCTION(BlueprintCallable, Category = "Building")
	void TryDemolish();

	UFUNCTION(BlueprintCallable, Category = "Building")
	void TryUpgrade();

	// Otvor/zatvor dvere, na ktore sa hrac pozera.
	UFUNCTION(BlueprintCallable, Category = "Building")
	void TryInteract();

	// --- Pre HUD ---

	UFUNCTION(BlueprintPure, Category = "Building")
	bool IsBuildMode() const { return bBuildMode; }

	UFUNCTION(BlueprintPure, Category = "Building")
	EBuildPieceType GetSelectedType() const { return SelectedType; }

	UFUNCTION(BlueprintPure, Category = "Building")
	bool IsPreviewValid() const { return bPreviewValid; }

	// Preco sa neda polozit (prazdne, ak sa da).
	UFUNCTION(BlueprintPure, Category = "Building")
	FText GetPreviewProblem() const { return PreviewProblem; }

	UFUNCTION(BlueprintPure, Category = "Building")
	FText GetSelectedName() const;

	UFUNCTION(BlueprintPure, Category = "Building")
	FText GetSelectedCostText() const;

	UFUNCTION(BlueprintPure, Category = "Building")
	ABuildPiece* GetLookedAtPiece() const;

	// Hlasky zo servera (malo materialu, obsadene...).
	UPROPERTY(BlueprintAssignable, Category = "Building")
	FOnBuildMessage OnBuildMessage;

	// --- Nastavenia ---

	// Ceny a HP dielov. ItemID musia sediet s ID v inventari.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TArray<FBuildPieceDef> PieceDefs;

	// Nasobok HP podla materialu: drevo, kamen, kov.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TArray<float> TierHealthMultiplier;

	// Predmety z inventara, ktore sa daju polozit (ID -> model).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TMap<FName, TObjectPtr<UStaticMesh>> PropMeshes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	float PropHealth = 150.f;

	// Priehladny material s vektorovym parametrom "Color". Bez neho je nahlad plny.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TObjectPtr<UMaterialInterface> GhostMaterial;

	// Vlastna Blueprint trieda dielu (napr. ine farby). Prazdne = ABuildPiece.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TSubclassOf<ABuildPiece> PieceClass;

	// Dosah stavania od oci postavy (cm).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	float BuildRange = 600.f;

	// Kolko materialu sa vrati pri zburani (0..1), znizene podla poskodenia.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building", meta = (ClampMin = "0", ClampMax = "1"))
	float DemolishRefund = 0.5f;

	// Stavanie zadarmo (na testovanie bez inventara).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	bool bFreeBuild = false;

	// Kratky text v rohu obrazovky (len v editore / development buildoch).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	bool bShowDebugText = true;

protected:
	UFUNCTION(Server, Reliable)
	void ServerPlace(const FBuildRequest& Req);

	UFUNCTION(Server, Reliable)
	void ServerDemolish(ABuildPiece* Piece);

	UFUNCTION(Server, Reliable)
	void ServerUpgrade(ABuildPiece* Piece);

	UFUNCTION(Server, Reliable)
	void ServerInteract(ABuildPiece* Piece);

	UFUNCTION(Client, Reliable)
	void ClientBuildMessage(const FText& Message);

private:
	APawn* GetPawn() const;
	APlayerController* GetPC() const;
	bool IsLocal() const;
	UBuildingSubsystem* GetSubsystem() const;

	const FBuildPieceDef* FindDef(EBuildPieceType Type) const;
	float GetMaxHealth(EBuildPieceType Type, EBuildTier Tier) const;
	TArray<FBuildCost> GetPlaceCost(const FBuildRequest& Req) const;

	bool TraceView(FHitResult& OutHit, FVector& OutViewLoc, FRotator& OutViewRot) const;
	ABuildPiece* FindGridPiece(const FHitResult& Hit) const;

	// Z pohladu hraca vyrata, kam by sa diel polozil. Vrati false, ak nie je kam.
	bool ComputeRequest(FBuildRequest& OutReq, FTransform& OutTransform) const;

	// Spolocna kontrola pre nahlad (klient) aj server.
	bool CheckPlacement(const FBuildRequest& Req, FTransform& OutTransform, FText& OutProblem) const;
	bool IsInRange(const FVector& Location) const;
	bool IsGrounded(const FVector& TopCenter) const;
	bool IsBlocked(const FBuildRequest& Req, const FTransform& Transform) const;

	void UpdatePreview();
	void DestroyPreview();
	void ShowMessage(const FText& Message);

	UPROPERTY(Transient)
	TObjectPtr<ABuildPiece> Preview;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> PreviewMesh;

	EBuildPieceType PreviewType = EBuildPieceType::Foundation;

	bool bBuildMode = false;
	EBuildPieceType SelectedType = EBuildPieceType::Foundation;
	FName SelectedPropItem;
	int32 RotationIndex = 0;

	FBuildRequest CurrentRequest;
	bool bPreviewValid = false;
	FText PreviewProblem;
	double LastPlaceTime = -1.0;
};
