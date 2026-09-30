#include "BuildInventory.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "UObject/TextProperty.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogBuildInventory, Log, All);

namespace
{
	// Nazvy funkcii inventara (bez medzier, podciarkovnikov a malymi pismenami), v poradi priority.
	const TCHAR* const AmountNames[] = { TEXT("getitemamount"), TEXT("getamount"), TEXT("getitemcount"), TEXT("getitemquantity"), TEXT("getquantity") };
	const TCHAR* const RemoveNames[] = { TEXT("removeitem"), TEXT("removeitems"), TEXT("removeitemamount"), TEXT("consumeitem") };
	const TCHAR* const AddNames[] = { TEXT("additem"), TEXT("additems"), TEXT("additemamount"), TEXT("giveitem") };

	void GetActors(APlayerController* PC, TArray<AActor*, TInlineAllocator<3>>& Out)
	{
		if (!PC)
		{
			return;
		}
		Out.Add(PC);
		if (APawn* Pawn = PC->GetPawn())
		{
			Out.Add(Pawn);
		}
		if (APlayerState* PS = PC->PlayerState)
		{
			Out.Add(PS);
		}
	}

	// Actor alebo komponent, ktory implementuje IBuildInventoryInterface.
	UObject* FindInterfaceObject(APlayerController* PC)
	{
		TArray<AActor*, TInlineAllocator<3>> Actors;
		GetActors(PC, Actors);
		for (AActor* A : Actors)
		{
			if (A->Implements<UBuildInventoryInterface>())
			{
				return A;
			}
		}
		for (AActor* A : Actors)
		{
			TInlineComponentArray<UActorComponent*> Comps(A);
			for (UActorComponent* C : Comps)
			{
				if (C && C->Implements<UBuildInventoryInterface>())
				{
					return C;
				}
			}
		}
		return nullptr;
	}

	UActorComponent* FindInventoryComponent(APlayerController* PC)
	{
		TArray<AActor*, TInlineAllocator<3>> Actors;
		GetActors(PC, Actors);
		for (AActor* A : Actors)
		{
			TInlineComponentArray<UActorComponent*> Comps(A);
			for (UActorComponent* C : Comps)
			{
				if (C && C->GetClass()->GetName().Contains(TEXT("SimpleInventorySystem")))
				{
					return C;
				}
			}
		}
		return nullptr;
	}

	FString NormalizeName(const FString& In)
	{
		return In.Replace(TEXT(" "), TEXT("")).Replace(TEXT("_"), TEXT("")).ToLower();
	}

	template <SIZE_T N>
	UFunction* FindFunction(const UObject* Obj, const TCHAR* const (&Names)[N])
	{
		for (const TCHAR* Wanted : Names)
		{
			for (TFieldIterator<UFunction> It(Obj->GetClass(), EFieldIteratorFlags::IncludeSuper); It; ++It)
			{
				if (NormalizeName(It->GetName()) == Wanted)
				{
					return *It;
				}
			}
		}
		return nullptr;
	}

	bool IsOutput(const FProperty* P)
	{
		return P->HasAnyPropertyFlags(CPF_ReturnParm)
			|| (P->HasAnyPropertyFlags(CPF_OutParm) && !P->HasAnyPropertyFlags(CPF_ReferenceParm));
	}

	struct FCallResult
	{
		bool bHasInt = false;
		int32 Int = 0;
		bool bHasBool = false;
		bool bBool = false;
	};

	// Zavola funkciu inventara cez reflexiu: prvy Name/String/Text parameter = ID predmetu, prvy int = mnozstvo.
	FCallResult CallInventoryFunction(UObject* Obj, UFunction* Func, FName ItemID, int32 Amount)
	{
		FCallResult Result;
		uint8* Parms = (uint8*)FMemory_Alloca_Aligned(FMath::Max<int32>(1, Func->ParmsSize), Func->GetMinAlignment());
		FMemory::Memzero(Parms, FMath::Max<int32>(1, Func->ParmsSize));

		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->InitializeValue_InContainer(Parms);
		}

		bool bIdSet = false;
		bool bAmountSet = false;
		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			FProperty* P = *It;
			if (IsOutput(P))
			{
				continue;
			}
			if (!bIdSet)
			{
				if (FNameProperty* NameProp = CastField<FNameProperty>(P))
				{
					NameProp->SetPropertyValue_InContainer(Parms, ItemID);
					bIdSet = true;
					continue;
				}
				if (FStrProperty* StrProp = CastField<FStrProperty>(P))
				{
					StrProp->SetPropertyValue_InContainer(Parms, ItemID.ToString());
					bIdSet = true;
					continue;
				}
				if (FTextProperty* TextProp = CastField<FTextProperty>(P))
				{
					TextProp->SetPropertyValue_InContainer(Parms, FText::FromName(ItemID));
					bIdSet = true;
					continue;
				}
			}
			if (!bAmountSet)
			{
				if (FIntProperty* IntProp = CastField<FIntProperty>(P))
				{
					IntProp->SetPropertyValue_InContainer(Parms, Amount);
					bAmountSet = true;
					continue;
				}
			}
		}

		if (!bIdSet)
		{
			UE_LOG(LogBuildInventory, Warning, TEXT("%s::%s nema parameter pre ID predmetu (Name/String/Text). Pouzi IBuildInventoryInterface."),
				*Obj->GetClass()->GetName(), *Func->GetName());
		}

		Obj->ProcessEvent(Func, Parms);

		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			FProperty* P = *It;
			if (!IsOutput(P))
			{
				continue;
			}
			if (FIntProperty* IntProp = CastField<FIntProperty>(P))
			{
				if (!Result.bHasInt)
				{
					Result.Int = IntProp->GetPropertyValue_InContainer(Parms);
					Result.bHasInt = true;
				}
			}
			else if (FBoolProperty* BoolProp = CastField<FBoolProperty>(P))
			{
				if (!Result.bHasBool)
				{
					Result.bBool = BoolProp->GetPropertyValue_InContainer(Parms);
					Result.bHasBool = true;
				}
			}
		}

		for (TFieldIterator<FProperty> It(Func); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->DestroyValue_InContainer(Parms);
		}
		return Result;
	}

	void WarnNoInventory(APlayerController* PC, const TCHAR* What)
	{
		static bool bWarned = false;
		if (!bWarned)
		{
			bWarned = true;
			UE_LOG(LogBuildInventory, Warning, TEXT("Stavanie: nenasiel som inventar (%s). Implementuj IBuildInventoryInterface alebo pridaj SimpleInventorySystem komponent."), What);
			FBuildInventory::LogInventoryApi(PC);
		}
	}
}

int32 FBuildInventory::GetAmount(APlayerController* PC, FName ItemID)
{
	if (UObject* Obj = FindInterfaceObject(PC))
	{
		return IBuildInventoryInterface::Execute_BuildGetItemAmount(Obj, ItemID);
	}
	if (UActorComponent* Inv = FindInventoryComponent(PC))
	{
		if (UFunction* Func = FindFunction(Inv, AmountNames))
		{
			const FCallResult R = CallInventoryFunction(Inv, Func, ItemID, 0);
			return R.bHasInt ? R.Int : 0;
		}
	}
	WarnNoInventory(PC, TEXT("Get Item Amount"));
	return 0;
}

bool FBuildInventory::Remove(APlayerController* PC, FName ItemID, int32 Amount)
{
	if (Amount <= 0)
	{
		return true;
	}
	if (UObject* Obj = FindInterfaceObject(PC))
	{
		return IBuildInventoryInterface::Execute_BuildRemoveItem(Obj, ItemID, Amount);
	}
	if (UActorComponent* Inv = FindInventoryComponent(PC))
	{
		if (UFunction* Func = FindFunction(Inv, RemoveNames))
		{
			const FCallResult R = CallInventoryFunction(Inv, Func, ItemID, Amount);
			return R.bHasBool ? R.bBool : true;
		}
	}
	WarnNoInventory(PC, TEXT("Remove Item"));
	return false;
}

bool FBuildInventory::Add(APlayerController* PC, FName ItemID, int32 Amount)
{
	if (Amount <= 0)
	{
		return true;
	}
	if (UObject* Obj = FindInterfaceObject(PC))
	{
		return IBuildInventoryInterface::Execute_BuildAddItem(Obj, ItemID, Amount);
	}
	if (UActorComponent* Inv = FindInventoryComponent(PC))
	{
		if (UFunction* Func = FindFunction(Inv, AddNames))
		{
			const FCallResult R = CallInventoryFunction(Inv, Func, ItemID, Amount);
			return R.bHasBool ? R.bBool : true;
		}
	}
	WarnNoInventory(PC, TEXT("Add Item"));
	return false;
}

bool FBuildInventory::HasCosts(APlayerController* PC, const TArray<FBuildCost>& Costs)
{
	// ten isty predmet moze byt v cene viackrat
	TMap<FName, int32> Needed;
	for (const FBuildCost& C : Costs)
	{
		if (!C.ItemID.IsNone() && C.Amount > 0)
		{
			Needed.FindOrAdd(C.ItemID) += C.Amount;
		}
	}
	for (const TPair<FName, int32>& N : Needed)
	{
		if (GetAmount(PC, N.Key) < N.Value)
		{
			return false;
		}
	}
	return true;
}

bool FBuildInventory::ConsumeCosts(APlayerController* PC, const TArray<FBuildCost>& Costs)
{
	if (!HasCosts(PC, Costs))
	{
		return false;
	}
	TArray<FBuildCost> Removed;
	for (const FBuildCost& C : Costs)
	{
		if (C.ItemID.IsNone() || C.Amount <= 0)
		{
			continue;
		}
		if (!Remove(PC, C.ItemID, C.Amount))
		{
			// vrat, co uz bolo odobrane
			for (const FBuildCost& R : Removed)
			{
				Add(PC, R.ItemID, R.Amount);
			}
			return false;
		}
		Removed.Add(C);
	}
	return true;
}

void FBuildInventory::LogInventoryApi(APlayerController* PC)
{
	if (UObject* Obj = FindInterfaceObject(PC))
	{
		UE_LOG(LogBuildInventory, Log, TEXT("Inventar cez IBuildInventoryInterface: %s"), *Obj->GetName());
		return;
	}
	UActorComponent* Inv = FindInventoryComponent(PC);
	if (!Inv)
	{
		TArray<AActor*, TInlineAllocator<3>> Actors;
		GetActors(PC, Actors);
		for (AActor* A : Actors)
		{
			TInlineComponentArray<UActorComponent*> Comps(A);
			for (UActorComponent* C : Comps)
			{
				if (C)
				{
					UE_LOG(LogBuildInventory, Log, TEXT("  komponent na %s: %s (%s)"), *A->GetName(), *C->GetName(), *C->GetClass()->GetName());
				}
			}
		}
		UE_LOG(LogBuildInventory, Warning, TEXT("SimpleInventorySystem komponent sa nenasiel na PlayerController / Pawn / PlayerState."));
		return;
	}

	UE_LOG(LogBuildInventory, Log, TEXT("Inventar: %s (%s)"), *Inv->GetName(), *Inv->GetClass()->GetName());
	for (TFieldIterator<UFunction> It(Inv->GetClass(), EFieldIteratorFlags::ExcludeSuper); It; ++It)
	{
		FString Params;
		for (TFieldIterator<FProperty> P(*It); P && P->HasAnyPropertyFlags(CPF_Parm); ++P)
		{
			Params += FString::Printf(TEXT("%s%s %s%s"), Params.IsEmpty() ? TEXT("") : TEXT(", "),
				*P->GetCPPType(), *P->GetName(), IsOutput(*P) ? TEXT(" [out]") : TEXT(""));
		}
		UE_LOG(LogBuildInventory, Log, TEXT("  %s(%s)"), *It->GetName(), *Params);
	}
}
