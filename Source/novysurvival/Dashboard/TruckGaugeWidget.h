// Pristrojovy panel kamiona na obrazovke (vpravo dole), cely sa kresli kodom - netreba ziadne textury.
// Otackomer s kontrolkami priamo v cifernikoch, digitalna rychlost a zaradeny prevodovy stupen v strede,
// pocitadlo km, priemerna spotreba a dva rucickove budiky: nafta a AdBlue.
// Pouzitie: Create Widget (trieda TruckGaugeWidget) -> Add to Viewport a kazdy tick nastavuj hodnoty.
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Styling/SlateBrush.h"
#include "TruckGaugeWidget.generated.h"

UENUM(BlueprintType)
enum class ETruckWarning : uint8
{
	TurnLeft		UMETA(DisplayName = "Smerovka vlavo"),
	TurnRight		UMETA(DisplayName = "Smerovka vpravo"),
	LowBeam			UMETA(DisplayName = "Stretne svetla"),
	HighBeam		UMETA(DisplayName = "Dialkove svetla"),
	ParkingBrake	UMETA(DisplayName = "Parkovacia brzda"),
	CheckEngine		UMETA(DisplayName = "Porucha motora"),
	GlowPlug		UMETA(DisplayName = "Zhavenie"),
	Battery			UMETA(DisplayName = "Dobijanie"),
	OilPressure		UMETA(DisplayName = "Tlak oleja"),
	CoolantTemp		UMETA(DisplayName = "Teplota chladiva"),
	Abs				UMETA(DisplayName = "ABS"),
	LowFuel			UMETA(DisplayName = "Rezerva nafty"),
	LowAdBlue		UMETA(DisplayName = "Malo AdBlue"),
	Count			UMETA(Hidden)
};

UCLASS()
class NOVYSURVIVAL_API UTruckGaugeWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UTruckGaugeWidget(const FObjectInitializer& ObjectInitializer);

	// --- Hodnoty z vozidla (nastavuj kazdy tick) ---

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje")
	float SpeedKmh = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje")
	float Rpm = 0.0f;

	/** Zaradeny stupen: 0 = N, -1 = R, 1 a viac = rychlost. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje")
	int32 Gear = 0;

	/** Nafta v nadrzi 0..1 (0 = prazdna, 1 = plna). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje", meta = (ClampMin = "0", ClampMax = "1"))
	float FuelLevel = 0.75f;

	/** AdBlue v nadrzi 0..1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje", meta = (ClampMin = "0", ClampMax = "1"))
	float AdBlueLevel = 0.6f;

	/** Priemerna spotreba v l/100 km (pocita sa sama cez AddTrip, alebo ju nastav). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje")
	float AverageConsumption = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje")
	float OdometerKm = 0.0f;

	// --- Nastavenie ---

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float MaxRpm = 3500.0f;

	/** Zelene (usporne) pasmo otacok. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float GreenRpmFrom = 1100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float GreenRpmTo = 1900.0f;

	/** Od tychto otacok je cervene pasmo. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float RedRpmFrom = 3000.0f;

	/** Velkost panelu (1 = priblizne tretina vysky obrazovky). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie", meta = (ClampMin = "0.3", ClampMax = "3"))
	float Scale = 1.0f;

	/** Ako rychlo rucicky dobiehaju hodnotu (vacsie = rychlejsie). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float NeedleSmoothing = 8.0f;

	/** Pod touto hodnotou sa rozsvieti rezerva nafty. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float LowFuelThreshold = 0.12f;

	/** Pod touto hodnotou sa rozsvieti kontrolka AdBlue. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	float LowAdBlueThreshold = 0.10f;

	/** Ukazka: panel sa hybe sam (na vyskusanie bez vozidla). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pristroje|Nastavenie")
	bool bDemoMode = false;

	// --- Funkcie ---

	/** Rychlost, otacky a stupen naraz. */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void SetVehicleState(float InSpeedKmh, float InRpm, int32 InGear);

	/** Zapne/vypne kontrolku (smerovky blikaju samy). */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void SetWarning(ETruckWarning Warning, bool bOn);

	/** Ci kontrolka prave svieti (aj automaticke: rezerva, AdBlue, test kontroliek). */
	UFUNCTION(BlueprintPure, Category = "Pristroje")
	bool IsWarningOn(ETruckWarning Warning) const;

	/** Zapalovanie: po zapnuti sa na chvilu rozsvietia vsetky kontrolky (test), po vypnuti panel zhasne. */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void SetIgnition(bool bOn);

	/** Motor bezi? Ked nebezi a zapalovanie je zapnute, svieti dobijanie a tlak oleja. */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void SetEngineRunning(bool bRunning);

	/** Pripocita prejdenu vzdialenost a spotrebovanu naftu - z toho sa pocita priemerna spotreba a km. */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void AddTrip(float DistanceKm, float FuelLiters);

	/** Vynuluje priemernu spotrebu (pocitadlo km ostava). */
	UFUNCTION(BlueprintCallable, Category = "Pristroje")
	void ResetTrip();

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	void TickDemo(float DeltaTime);

	uint32 WarningMask = 0;
	bool bIgnitionOn = true;
	bool bEngineRunning = true;
	float LampTestTime = 0.0f;
	float BlinkTime = 0.0f;
	float DemoTime = 0.0f;
	float TripKm = 0.0f;
	float TripLiters = 0.0f;

	float ShownRpm = 0.0f;
	float ShownSpeed = 0.0f;
	float ShownFuel = 0.0f;
	float ShownAdBlue = 0.0f;

	FSlateBrush CircleBrush;
	FSlateBrush SolidBrush;
};
