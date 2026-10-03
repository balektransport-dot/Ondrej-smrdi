#include "DirtContainerComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"

UDirtContainerComponent::UDirtContainerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UDirtContainerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UDirtContainerComponent, Dirt);
	DOREPLIFETIME(UDirtContainerComponent, Gold);
}

void UDirtContainerComponent::BeginPlay()
{
	Super::BeginPlay();
	if (FillVisual)
	{
		FillVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		FillVisual->SetCastShadow(false);
	}
	UpdateVisual();
}

FDirtLoad UDirtContainerComponent::AddLoad(const FDirtLoad& Load)
{
	if (Load.IsEmpty())
	{
		return FDirtLoad();
	}
	const float Accepted = FMath::Min(Load.Dirt, GetFreeSpace());
	const float Fraction = Accepted / Load.Dirt;
	Dirt += Accepted;
	Gold += Load.Gold * Fraction;
	UpdateVisual();
	return FDirtLoad(Load.Dirt - Accepted, Load.Gold * (1.f - Fraction));
}

FDirtLoad UDirtContainerComponent::TakeLoad(float Amount)
{
	const float Taken = FMath::Clamp(Amount, 0.f, Dirt);
	if (Taken <= 0.f)
	{
		return FDirtLoad();
	}
	const float GoldTaken = Gold * (Taken / Dirt);
	Dirt -= Taken;
	Gold -= GoldTaken;
	if (Dirt <= 0.001f)
	{
		Dirt = 0.f;
		Gold = 0.f;
	}
	UpdateVisual();
	return FDirtLoad(Taken, GoldTaken);
}

bool UDirtContainerComponent::AcceptsPoint(const FVector& WorldPoint) const
{
	const FVector Local = GetComponentTransform().InverseTransformPositionNoScale(WorldPoint);
	const float Margin = 40.f;
	return FMath::Abs(Local.X) <= FillSize.X * 0.5f + Margin
		&& FMath::Abs(Local.Y) <= FillSize.Y * 0.5f + Margin
		&& Local.Z >= -60.f;
}

void UDirtContainerComponent::OnRep_Load()
{
	UpdateVisual();
}

void UDirtContainerComponent::UpdateVisual()
{
	if (!FillVisual)
	{
		return;
	}
	const float Fraction = Capacity > 0.f ? FMath::Clamp(Dirt / Capacity, 0.f, 1.f) : 0.f;
	FillVisual->SetVisibility(Fraction > 0.01f);
	// kopa rastie od dna nahor
	const float Height = FMath::Max(1.f, FillSize.Z * Fraction);
	FillVisual->SetRelativeLocation(FVector(0.f, 0.f, Height * 0.5f));
	FillVisual->SetRelativeScale3D(FVector(FillSize.X, FillSize.Y, Height) / 100.f);
}
