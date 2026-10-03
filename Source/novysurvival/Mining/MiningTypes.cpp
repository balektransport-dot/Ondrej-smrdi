#include "MiningTypes.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// Zakladne tvary enginu maju 100 cm a pivot v strede.
	UStaticMesh* GetShapeMesh(ELowPolyShape Shape)
	{
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
		switch (Shape)
		{
		case ELowPolyShape::Cylinder: return Cylinder.Object;
		case ELowPolyShape::Sphere:   return Sphere.Object;
		case ELowPolyShape::Cone:     return Cone.Object;
		default:                      return Cube.Object;
		}
	}

	UMaterialInterface* GetBaseMaterial()
	{
		static ConstructorHelpers::FObjectFinder<UMaterialInterface> Mat(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
		return Mat.Object;
	}
}

UStaticMeshComponent* FLowPolyParts::Add(AActor* Owner, const TCHAR* Name, USceneComponent* Parent, ELowPolyShape Shape,
	const FVector& Location, const FVector& SizeCm, const FLinearColor& Color, const FRotator& Rotation)
{
	UStaticMeshComponent* Part = Owner->CreateDefaultSubobject<UStaticMeshComponent>(Name);
	Part->SetupAttachment(Parent);
	Part->SetStaticMesh(GetShapeMesh(Shape));
	Part->SetRelativeLocationAndRotation(Location, Rotation);
	Part->SetRelativeScale3D(SizeCm / 100.f);
	Part->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	Part->SetCanEverAffectNavigation(false);
	Parts.Add(Part);
	Colors.Add(Color);
	if (!Material)
	{
		Material = GetBaseMaterial();
	}
	return Part;
}

void FLowPolyParts::ApplyColors(UObject* Outer)
{
	if (!Material)
	{
		return;
	}
	// jeden material na farbu
	TMap<FLinearColor, UMaterialInstanceDynamic*> ByColor;
	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		if (!Parts[i] || !Colors.IsValidIndex(i))
		{
			continue;
		}
		UMaterialInstanceDynamic*& MID = ByColor.FindOrAdd(Colors[i]);
		if (!MID)
		{
			MID = UMaterialInstanceDynamic::Create(Material, Outer);
			MID->SetVectorParameterValue(TEXT("Color"), Colors[i]);
		}
		Parts[i]->SetMaterial(0, MID);
	}
}
