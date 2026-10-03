// Tazba zlata – spolocne typy: naklad hliny a low poly diely z jednoduchych tvarov.
#pragma once

#include "CoreMinimal.h"
#include "MiningTypes.generated.h"

class AActor;
class USceneComponent;
class UStaticMeshComponent;
class UMaterialInterface;

// Hlina v tonach a zlato v nej v gramoch.
USTRUCT(BlueprintType)
struct FDirtLoad
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float Dirt = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mining")
	float Gold = 0.f;

	FDirtLoad() = default;
	FDirtLoad(float InDirt, float InGold) : Dirt(InDirt), Gold(InGold) {}

	bool IsEmpty() const { return Dirt <= KINDA_SMALL_NUMBER; }
};

UENUM()
enum class ELowPolyShape : uint8
{
	Cube,
	Cylinder,
	Sphere,
	Cone
};

namespace MiningColors
{
	const FLinearColor Yellow(0.85f, 0.55f, 0.05f);
	const FLinearColor Orange(0.80f, 0.25f, 0.04f);
	const FLinearColor Dark(0.05f, 0.05f, 0.05f);
	const FLinearColor Steel(0.30f, 0.32f, 0.35f);
	const FLinearColor Glass(0.20f, 0.35f, 0.45f);
	const FLinearColor Dirt(0.25f, 0.14f, 0.06f);
	const FLinearColor Waste(0.45f, 0.38f, 0.28f);
	const FLinearColor Gold(1.00f, 0.70f, 0.10f);
	const FLinearColor Green(0.10f, 0.35f, 0.15f);
}

// Diely actora z kociek/valcov s jednou farbou (low poly vzhlad bez modelov).
USTRUCT()
struct FLowPolyParts
{
	GENERATED_BODY()

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> Parts;

	UPROPERTY()
	TArray<FLinearColor> Colors;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> Material;

	// Volat len v konstruktore actora. SizeCm = rozmer dielu v cm.
	UStaticMeshComponent* Add(AActor* Owner, const TCHAR* Name, USceneComponent* Parent, ELowPolyShape Shape,
		const FVector& Location, const FVector& SizeCm, const FLinearColor& Color, const FRotator& Rotation = FRotator::ZeroRotator);

	// Volat v BeginPlay – nastavi farby.
	void ApplyColors(UObject* Outer);
};
