// Napojenie stavania na inventar.
// 1) Ak PlayerController (alebo Pawn) implementuje IBuildInventoryInterface, pouzije sa to.
// 2) Inak sa najde komponent "*SimpleInventorySystem*" a jeho funkcie
//    (Get Item Amount / Remove Item / Add Item) sa zavolaju cez reflexiu.
#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "BuildTypes.h"
#include "BuildInventory.generated.h"

class APlayerController;

UINTERFACE(BlueprintType, Blueprintable)
class UBuildInventoryInterface : public UInterface
{
	GENERATED_BODY()
};

class NOVYSURVIVAL_API IBuildInventoryInterface
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Building")
	int32 BuildGetItemAmount(FName ItemID);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Building")
	bool BuildRemoveItem(FName ItemID, int32 Amount);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Building")
	bool BuildAddItem(FName ItemID, int32 Amount);
};

struct NOVYSURVIVAL_API FBuildInventory
{
	static int32 GetAmount(APlayerController* PC, FName ItemID);
	static bool Remove(APlayerController* PC, FName ItemID, int32 Amount);
	static bool Add(APlayerController* PC, FName ItemID, int32 Amount);

	static bool HasCosts(APlayerController* PC, const TArray<FBuildCost>& Costs);
	static bool ConsumeCosts(APlayerController* PC, const TArray<FBuildCost>& Costs);

	// Vypise do Output Logu funkcie inventara a ich parametre (na ladenie).
	static void LogInventoryApi(APlayerController* PC);
};
