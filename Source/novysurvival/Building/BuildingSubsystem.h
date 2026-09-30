// Evidencia obsadenych slotov v mriezke + jednoducha statika.
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "BuildTypes.h"
#include "BuildingSubsystem.generated.h"

class ABuildPiece;

struct FBuildSlotKey
{
	FIntVector Frame;
	int32 FrameYaw = 0;
	FIntVector Cell;
	uint8 Slot = 0;

	bool operator==(const FBuildSlotKey& O) const
	{
		return Frame == O.Frame && FrameYaw == O.FrameYaw && Cell == O.Cell && Slot == O.Slot;
	}

	friend uint32 GetTypeHash(const FBuildSlotKey& K)
	{
		uint32 H = GetTypeHash(K.Frame);
		H = HashCombine(H, GetTypeHash(K.FrameYaw));
		H = HashCombine(H, GetTypeHash(K.Cell));
		return HashCombine(H, GetTypeHash(K.Slot));
	}
};

UCLASS()
class NOVYSURVIVAL_API UBuildingSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	static FBuildSlotKey MakeKey(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot);

	void Register(ABuildPiece* Piece);
	void Unregister(ABuildPiece* Piece);

	ABuildPiece* GetPiece(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot) const;
	bool IsFree(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot) const;

	// Drzi tento diel nieco? (zaklad vzdy ano)
	bool IsSupported(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot, EBuildPieceType Type) const;

	// Server: po zniceni dielu zburaj susedov, ktore uz nic nedrzi.
	void QueueStabilityCheck(const FVector& Origin, float Yaw, const FIntVector& Cell);

private:
	bool HasFloor(const FVector& O, float Y, const FIntVector& C) const;
	bool HasEdge(const FVector& O, float Y, const FIntVector& C, EBuildSlot S) const;
	bool IsFloorDirectlySupported(const FVector& O, float Y, const FIntVector& C) const;
	void RunStabilityCheck(FVector Origin, float Yaw, FIntVector Cell);

	TMap<FBuildSlotKey, TWeakObjectPtr<ABuildPiece>> Slots;
};
