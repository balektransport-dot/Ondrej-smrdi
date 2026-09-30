#include "BuildingSubsystem.h"
#include "BuildPiece.h"
#include "Engine/World.h"
#include "TimerManager.h"

FBuildSlotKey UBuildingSubsystem::MakeKey(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot)
{
	FBuildSlotKey K;
	K.Frame = FIntVector(FMath::RoundToInt(Origin.X), FMath::RoundToInt(Origin.Y), FMath::RoundToInt(Origin.Z));
	K.FrameYaw = FMath::RoundToInt(FRotator::NormalizeAxis(Yaw) * 10.f);
	K.Cell = Cell;
	K.Slot = (uint8)Slot;
	return K;
}

void UBuildingSubsystem::Register(ABuildPiece* Piece)
{
	Slots.Add(MakeKey(Piece->GridOrigin, Piece->GridYaw, Piece->Cell, Piece->Slot), Piece);
}

void UBuildingSubsystem::Unregister(ABuildPiece* Piece)
{
	const FBuildSlotKey K = MakeKey(Piece->GridOrigin, Piece->GridYaw, Piece->Cell, Piece->Slot);
	if (const TWeakObjectPtr<ABuildPiece>* Found = Slots.Find(K))
	{
		if (!Found->IsValid() || Found->Get() == Piece)
		{
			Slots.Remove(K);
		}
	}
}

ABuildPiece* UBuildingSubsystem::GetPiece(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot) const
{
	const TWeakObjectPtr<ABuildPiece>* Found = Slots.Find(MakeKey(Origin, Yaw, Cell, Slot));
	ABuildPiece* P = Found ? Found->Get() : nullptr;
	return (P && !P->IsActorBeingDestroyed()) ? P : nullptr;
}

bool UBuildingSubsystem::IsFree(const FVector& Origin, float Yaw, const FIntVector& Cell, EBuildSlot Slot) const
{
	return GetPiece(Origin, Yaw, Cell, Slot) == nullptr;
}

bool UBuildingSubsystem::HasFloor(const FVector& O, float Y, const FIntVector& C) const
{
	ABuildPiece* P = GetPiece(O, Y, C, EBuildSlot::Floor);
	return P && P->PieceType != EBuildPieceType::Roof;
}

bool UBuildingSubsystem::HasEdge(const FVector& O, float Y, const FIntVector& C, EBuildSlot S) const
{
	return GetPiece(O, Y, C, S) != nullptr;
}

bool UBuildingSubsystem::IsFloorDirectlySupported(const FVector& O, float Y, const FIntVector& C) const
{
	ABuildPiece* Self = GetPiece(O, Y, C, EBuildSlot::Floor);
	if (Self && Self->PieceType == EBuildPieceType::Foundation)
	{
		return true;
	}
	// stena pod niektorou zo 4 hran bunky
	const FIntVector B = C - FIntVector(0, 0, 1);
	return HasEdge(O, Y, B, EBuildSlot::EdgeX) || HasEdge(O, Y, B - FIntVector(1, 0, 0), EBuildSlot::EdgeX)
		|| HasEdge(O, Y, B, EBuildSlot::EdgeY) || HasEdge(O, Y, B - FIntVector(0, 1, 0), EBuildSlot::EdgeY);
}

bool UBuildingSubsystem::IsSupported(const FVector& O, float Y, const FIntVector& C, EBuildSlot Slot, EBuildPieceType Type) const
{
	switch (Slot)
	{
	case EBuildSlot::Floor:
	{
		if (Type == EBuildPieceType::Foundation)
		{
			return true;
		}
		const FIntVector B = C - FIntVector(0, 0, 1);
		if (HasEdge(O, Y, B, EBuildSlot::EdgeX) || HasEdge(O, Y, B - FIntVector(1, 0, 0), EBuildSlot::EdgeX)
			|| HasEdge(O, Y, B, EBuildSlot::EdgeY) || HasEdge(O, Y, B - FIntVector(0, 1, 0), EBuildSlot::EdgeY))
		{
			return true;
		}
		// previs max. 1 bunka od podopretej podlahy / zakladu
		static const FIntVector Dirs[] = { FIntVector(1, 0, 0), FIntVector(-1, 0, 0), FIntVector(0, 1, 0), FIntVector(0, -1, 0) };
		for (const FIntVector& D : Dirs)
		{
			if (HasFloor(O, Y, C + D) && IsFloorDirectlySupported(O, Y, C + D))
			{
				return true;
			}
		}
		return false;
	}
	case EBuildSlot::EdgeX:
	case EBuildSlot::EdgeY:
	{
		const FIntVector Across = Slot == EBuildSlot::EdgeX ? FIntVector(1, 0, 0) : FIntVector(0, 1, 0);
		return HasFloor(O, Y, C) || HasFloor(O, Y, C + Across) || HasEdge(O, Y, C - FIntVector(0, 0, 1), Slot);
	}
	case EBuildSlot::DoorX:
	case EBuildSlot::DoorY:
	{
		ABuildPiece* Frame = GetPiece(O, Y, C, Slot == EBuildSlot::DoorX ? EBuildSlot::EdgeX : EBuildSlot::EdgeY);
		return Frame && Frame->PieceType == EBuildPieceType::Doorway;
	}
	default:
		return true;
	}
}

void UBuildingSubsystem::QueueStabilityCheck(const FVector& Origin, float Yaw, const FIntVector& Cell)
{
	if (UWorld* World = GetWorld())
	{
		TWeakObjectPtr<UBuildingSubsystem> WeakThis(this);
		World->GetTimerManager().SetTimerForNextTick([WeakThis, Origin, Yaw, Cell]()
		{
			if (WeakThis.IsValid())
			{
				WeakThis->RunStabilityCheck(Origin, Yaw, Cell);
			}
		});
	}
}

void UBuildingSubsystem::RunStabilityCheck(FVector Origin, float Yaw, FIntVector Cell)
{
	static const EBuildSlot AllSlots[] = { EBuildSlot::Floor, EBuildSlot::EdgeX, EBuildSlot::EdgeY, EBuildSlot::DoorX, EBuildSlot::DoorY };

	TArray<ABuildPiece*> ToDestroy;
	for (int32 dz = 0; dz <= 1; ++dz)
	for (int32 dy = -1; dy <= 1; ++dy)
	for (int32 dx = -1; dx <= 1; ++dx)
	{
		const FIntVector C = Cell + FIntVector(dx, dy, dz);
		for (EBuildSlot S : AllSlots)
		{
			ABuildPiece* P = GetPiece(Origin, Yaw, C, S);
			if (P && P->HasAuthority() && !IsSupported(Origin, Yaw, C, S, P->PieceType))
			{
				ToDestroy.AddUnique(P);
			}
		}
	}
	// Destroy -> EndPlay -> dalsia kontrola o tick neskor (retazove zrutenie)
	for (ABuildPiece* P : ToDestroy)
	{
		P->Destroy();
	}
}
