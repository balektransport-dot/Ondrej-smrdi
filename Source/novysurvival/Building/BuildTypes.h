// Stavebny system – spolocne typy a mriezka.
#pragma once

#include "CoreMinimal.h"
#include "BuildTypes.generated.h"

UENUM(BlueprintType)
enum class EBuildPieceType : uint8
{
	Foundation,
	Floor,
	Wall,
	Doorway,
	Door,
	Roof,
	Prop // volne polozeny predmet z inventara (pec, stol...)
};

UENUM(BlueprintType)
enum class EBuildTier : uint8
{
	Wood,
	Stone,
	Metal
};

// Miesto v bunke mriezky. EdgeX = hrana na +X strane bunky, EdgeY = na +Y strane.
UENUM(BlueprintType)
enum class EBuildSlot : uint8
{
	Floor,  // zaklad / podlaha / strecha
	EdgeX,  // stena / zarubna
	EdgeY,
	DoorX,  // dvere v zarubni
	DoorY,
	None    // Prop
};

USTRUCT(BlueprintType)
struct FBuildCost
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	FName ItemID;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	int32 Amount = 1;
};

// Definicia jedneho typu stavebneho dielu (cena a HP podla materialu).
USTRUCT(BlueprintType)
struct FBuildPieceDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	EBuildPieceType Type = EBuildPieceType::Wall;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	FText Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	float BaseHealth = 200.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TArray<FBuildCost> WoodCost;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TArray<FBuildCost> StoneCost;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
	TArray<FBuildCost> MetalCost;

	const TArray<FBuildCost>& GetCost(EBuildTier Tier) const
	{
		switch (Tier)
		{
		case EBuildTier::Stone: return StoneCost;
		case EBuildTier::Metal: return MetalCost;
		default:                return WoodCost;
		}
	}
};

// Poziadavka na polozenie (klient -> server).
USTRUCT()
struct FBuildRequest
{
	GENERATED_BODY()

	UPROPERTY() EBuildPieceType Type = EBuildPieceType::Foundation;
	UPROPERTY() FName ItemID;
	UPROPERTY() bool bSnapped = true;
	UPROPERTY() FVector GridOrigin = FVector::ZeroVector;
	UPROPERTY() float GridYaw = 0.f;
	UPROPERTY() FIntVector Cell = FIntVector::ZeroValue;
	UPROPERTY() EBuildSlot Slot = EBuildSlot::Floor;
	UPROPERTY() int32 RoofDir = 0;
	UPROPERTY() FVector FreeLocation = FVector::ZeroVector;
	UPROPERTY() float FreeYaw = 0.f;
};

// Box dielu v lokalnych suradniciach actora (velkost v cm).
struct FBuildBox
{
	FVector Center;
	FVector Size;
	FRotator Rot = FRotator::ZeroRotator;
};

namespace BuildGrid
{
	constexpr float Cell = 300.f;       // sirka bunky (cm)
	constexpr float Height = 300.f;     // vyska poschodia (cm)
	constexpr float WallThick = 20.f;
	constexpr float FloorThick = 20.f;
	constexpr float FoundationHeight = 100.f;
	constexpr float DoorWidth = 110.f;
	constexpr float DoorHeight = 220.f;

	inline FVector LocalToWorld(const FVector& Origin, float Yaw, const FVector& Local)
	{
		return Origin + FRotator(0.f, Yaw, 0.f).RotateVector(Local);
	}

	inline FVector WorldToLocal(const FVector& Origin, float Yaw, const FVector& World)
	{
		return FRotator(0.f, Yaw, 0.f).UnrotateVector(World - Origin);
	}

	inline bool IsEdge(EBuildSlot S) { return S == EBuildSlot::EdgeX || S == EBuildSlot::EdgeY; }
	inline bool IsDoor(EBuildSlot S) { return S == EBuildSlot::DoorX || S == EBuildSlot::DoorY; }

	// Svetova transformacia dielu v danom slote.
	inline FTransform SlotTransform(const FVector& Origin, float Yaw, const FIntVector& C, EBuildSlot Slot, int32 RoofDir)
	{
		FVector L(C.X * Cell, C.Y * Cell, C.Z * Height);
		float LocalYaw = 0.f;
		if (Slot == EBuildSlot::EdgeX || Slot == EBuildSlot::DoorX) { L.X += Cell * 0.5f; LocalYaw = 90.f; }
		else if (Slot == EBuildSlot::EdgeY || Slot == EBuildSlot::DoorY) { L.Y += Cell * 0.5f; }
		else if (Slot == EBuildSlot::Floor) { LocalYaw = 90.f * RoofDir; }
		return FTransform(FRotator(0.f, Yaw + LocalYaw, 0.f), LocalToWorld(Origin, Yaw, L));
	}

	// Tvar dielu z kociek (/Engine/BasicShapes/Cube = 100 cm).
	inline void GetShape(EBuildPieceType Type, TArray<FBuildBox>& Out)
	{
		Out.Reset();
		switch (Type)
		{
		case EBuildPieceType::Foundation:
			Out.Add({ FVector(0, 0, -FoundationHeight * 0.5f), FVector(Cell, Cell, FoundationHeight) });
			break;
		case EBuildPieceType::Floor:
			Out.Add({ FVector(0, 0, -FloorThick * 0.5f), FVector(Cell, Cell, FloorThick) });
			break;
		case EBuildPieceType::Wall:
			Out.Add({ FVector(0, 0, Height * 0.5f), FVector(Cell, WallThick, Height) });
			break;
		case EBuildPieceType::Doorway:
		{
			const float Side = (Cell - DoorWidth) * 0.5f;
			Out.Add({ FVector(-(DoorWidth + Side) * 0.5f, 0, Height * 0.5f), FVector(Side, WallThick, Height) });
			Out.Add({ FVector((DoorWidth + Side) * 0.5f, 0, Height * 0.5f), FVector(Side, WallThick, Height) });
			Out.Add({ FVector(0, 0, (DoorHeight + Height) * 0.5f), FVector(DoorWidth, WallThick, Height - DoorHeight) });
			break;
		}
		case EBuildPieceType::Door:
			// relativne k pantu (pant je na X = -DoorWidth/2)
			Out.Add({ FVector(DoorWidth * 0.5f, 0, DoorHeight * 0.5f), FVector(DoorWidth - 4.f, 6.f, DoorHeight - 2.f) });
			break;
		case EBuildPieceType::Roof:
			// sikma doska 45 stupnov, stupa v smere +X
			Out.Add({ FVector(0, 0, Height * 0.5f), FVector(Cell * 1.4142f, Cell, FloorThick), FRotator(45.f, 0.f, 0.f) });
			break;
		default:
			break;
		}
	}
}
