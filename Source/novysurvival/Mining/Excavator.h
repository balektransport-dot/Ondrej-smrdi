// Pasovy bager: otocna kabina, vyloznik, rameno a lopata. Lopata nabera hlinu z kop (ADigSite)
// a vysypava ju do korby, nasypky alebo na zem.
#pragma once

#include "CoreMinimal.h"
#include "MiningVehicle.h"
#include "Excavator.generated.h"

class UDirtContainerComponent;

UCLASS()
class NOVYSURVIVAL_API AExcavator : public AMiningVehicle
{
	GENERATED_BODY()

public:
	AExcavator();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintPure, Category = "Mining")
	UDirtContainerComponent* GetBucket() const { return Bucket; }

	// Rychlosti (stupne/s, lopata = cast pohybu za s).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float SwingRate = 40.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float BoomRate = 25.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float StickRate = 35.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float BucketRate = 0.9f;

	// Kolko ton naberie za sekundu, ked sa lopata zatvara v hline.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float DigRate = 1.5f;

	// Kolko ton vysype za sekundu, ked je lopata otvorena.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining|Arm")
	float DumpRate = 2.f;

protected:
	virtual void UpdateControls(APlayerController* PC, float DeltaTime) override;
	virtual FString GetStatusText() const override;

	UFUNCTION()
	void OnRep_Arm();

	void ApplyArm();
	void UpdateBucket(float Input, float DeltaTime);

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> Upper;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> BoomPivot;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> StickPivot;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> BucketPivot;

	// Spicka lopaty – tu sa zistuje, ci je lopata v hline.
	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<USceneComponent> BucketTip;

	UPROPERTY(VisibleAnywhere, Category = "Mining")
	TObjectPtr<UDirtContainerComponent> Bucket;

	// Uhly ramena (replikovane, aby ich videli aj ostatni hraci).
	UPROPERTY(ReplicatedUsing = OnRep_Arm)
	float SwingYaw = 0.f;

	UPROPERTY(ReplicatedUsing = OnRep_Arm)
	float BoomPitch = 30.f;

	UPROPERTY(ReplicatedUsing = OnRep_Arm)
	float StickPitch = -100.f;

	// 0 = lopata otvorena (sype), 1 = zatvorena (drzi hlinu).
	UPROPERTY(ReplicatedUsing = OnRep_Arm)
	float BucketCurl = 0.7f;
};
