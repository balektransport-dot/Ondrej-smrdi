#include "TruckGaugeWidget.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "Misc/EngineVersionComparison.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"

// pomocky na kreslenie (vlastny menny priestor, aby sa nebili s inymi subormi pri unity builde)
namespace TruckGaugeDraw
{
#if UE_VERSION_OLDER_THAN(5, 2, 0)
	using FGaugeVec = FVector2D;
#else
	using FGaugeVec = FVector2f;
#endif

	const FLinearColor WhiteCol(0.93f, 0.94f, 0.96f, 1.0f);
	const FLinearColor FaceCol(0.012f, 0.015f, 0.02f, 0.82f);
	const FLinearColor BezelCol(0.32f, 0.34f, 0.38f, 1.0f);
	const FLinearColor GreenCol(0.2f, 0.78f, 0.28f, 1.0f);
	const FLinearColor RedCol(0.9f, 0.14f, 0.1f, 1.0f);
	const FLinearColor NeedleCol(1.0f, 0.12f, 0.05f, 1.0f);
	const FLinearColor HubCol(0.12f, 0.13f, 0.15f, 1.0f);
	const FLinearColor OdoCol(0.0f, 0.0f, 0.0f, 0.65f);
	const FLinearColor LampOffCol(0.6f, 0.62f, 0.66f, 0.16f);
	const FLinearColor LampGreen(0.15f, 0.9f, 0.25f, 1.0f);
	const FLinearColor LampBlue(0.15f, 0.45f, 1.0f, 1.0f);
	const FLinearColor LampRed(1.0f, 0.15f, 0.1f, 1.0f);
	const FLinearColor LampAmber(1.0f, 0.62f, 0.05f, 1.0f);

	FLinearColor Dimmed(const FLinearColor& Color, bool bLit)
	{
		return bLit ? Color : FLinearColor(Color.R * 0.35f, Color.G * 0.35f, Color.B * 0.35f, Color.A * 0.6f);
	}

	FLinearColor LampColor(ETruckWarning Warning)
	{
		switch (Warning)
		{
		case ETruckWarning::TurnLeft:
		case ETruckWarning::TurnRight:
		case ETruckWarning::LowBeam:
			return LampGreen;
		case ETruckWarning::HighBeam:
			return LampBlue;
		case ETruckWarning::ParkingBrake:
		case ETruckWarning::Battery:
		case ETruckWarning::OilPressure:
		case ETruckWarning::CoolantTemp:
			return LampRed;
		default:
			return LampAmber;
		}
	}

	// smer pod uhlom v stupnoch: 0 = hore, kladne v smere hodinovych ruciciek (os Y v Slate ide dole)
	FVector2D Dir(float Deg)
	{
		const float Rad = FMath::DegreesToRadians(Deg);
		return FVector2D(FMath::Sin(Rad), -FMath::Cos(Rad));
	}

	struct FGaugePainter
	{
		const FGeometry& Geometry;
		FSlateWindowElementList& Out;
		int32 Layer;
		const FSlateBrush& CircleBrush;
		const FSlateBrush& SolidBrush;

		void Lines(const TArray<FVector2D>& Points, const FLinearColor& Color, float Thickness, int32 Offset = 1) const
		{
			if (Points.Num() < 2)
			{
				return;
			}
			TArray<FGaugeVec> Converted;
			Converted.Reserve(Points.Num());
			for (const FVector2D& V : Points)
			{
				Converted.Add(FGaugeVec((float)V.X, (float)V.Y));
			}
			FSlateDrawElement::MakeLines(Out, Layer + Offset, Geometry.ToPaintGeometry(), MoveTemp(Converted),
				ESlateDrawEffect::None, Color, true, Thickness);
		}

		void Line(const FVector2D& A, const FVector2D& B, const FLinearColor& Color, float Thickness, int32 Offset = 1) const
		{
			Lines(TArray<FVector2D>{A, B}, Color, Thickness, Offset);
		}

		void Arc(const FVector2D& C, float Radius, float A0, float A1, const FLinearColor& Color, float Thickness, int32 Offset = 1) const
		{
			const int32 N = FMath::Clamp(FMath::CeilToInt(FMath::Abs(A1 - A0) / 6.0f), 2, 90);
			TArray<FVector2D> Points;
			Points.Reserve(N + 1);
			for (int32 i = 0; i <= N; ++i)
			{
				Points.Add(C + Dir(FMath::Lerp(A0, A1, (float)i / N)) * Radius);
			}
			Lines(Points, Color, Thickness, Offset);
		}

		// lomena ciara z bodov v rozsahu -1..1, zvacsena na polovicnu velkost S okolo stredu C
		void Shape(const FVector2D& C, float S, std::initializer_list<FVector2D> Points, bool bClosed, const FLinearColor& Color,
			float Thickness, int32 Offset = 3) const
		{
			TArray<FVector2D> Scaled;
			for (const FVector2D& V : Points)
			{
				Scaled.Add(C + V * S);
			}
			if (bClosed && Scaled.Num() > 0)
			{
				Scaled.Add(Scaled[0]);
			}
			Lines(Scaled, Color, Thickness, Offset);
		}

		void Disc(const FVector2D& C, float Radius, const FLinearColor& Color, int32 Offset = 0) const
		{
			const FVector2D Size(Radius * 2.0f, Radius * 2.0f);
			FSlateDrawElement::MakeBox(Out, Layer + Offset,
				Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(C - Size * 0.5f)), &CircleBrush, ESlateDrawEffect::None, Color);
		}

		void Rect(const FVector2D& Center, const FVector2D& Size, const FLinearColor& Color, int32 Offset = 0) const
		{
			FSlateDrawElement::MakeBox(Out, Layer + Offset,
				Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Center - Size * 0.5f)), &SolidBrush, ESlateDrawEffect::None, Color);
		}

		// text vycentrovany na bod, Height = priblizna vyska pisma
		void Text(const FString& String, const FVector2D& Center, float Height, const FLinearColor& Color, bool bBold = true,
			int32 Offset = 2) const
		{
			const int32 FontSize = FMath::Max(1, FMath::RoundToInt(Height * 0.75f));
			const FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), FontSize);
			const TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
			const FVector2D TextSize = Measure->Measure(String, Font);
			FSlateDrawElement::MakeText(Out, Layer + Offset,
				Geometry.ToPaintGeometry(TextSize, FSlateLayoutTransform(Center - TextSize * 0.5f)), String, Font,
				ESlateDrawEffect::None, Color);
		}
	};

	// ikonky kontroliek (jednoduche ciarove piktogramy), S = polovicna velkost ikonky
	void DrawIcon(const FGaugePainter& P, ETruckWarning Warning, const FVector2D& C, float S, const FLinearColor& Col)
	{
		const float T = FMath::Max(1.2f, S * 0.16f);
		switch (Warning)
		{
		case ETruckWarning::TurnLeft:
		case ETruckWarning::TurnRight:
		{
			const float M = Warning == ETruckWarning::TurnLeft ? 1.0f : -1.0f;
			P.Shape(C, S, {FVector2D(-1.0f * M, 0.0f), FVector2D(-0.15f * M, -0.75f), FVector2D(-0.15f * M, -0.3f),
				FVector2D(0.85f * M, -0.3f), FVector2D(0.85f * M, 0.3f), FVector2D(-0.15f * M, 0.3f), FVector2D(-0.15f * M, 0.75f)},
				true, Col, T);
			break;
		}
		case ETruckWarning::LowBeam:
		case ETruckWarning::HighBeam:
		{
			P.Shape(C, S, {FVector2D(0.05f, -0.7f), FVector2D(0.45f, -0.68f), FVector2D(0.75f, -0.45f), FVector2D(0.9f, 0.0f),
				FVector2D(0.75f, 0.45f), FVector2D(0.45f, 0.68f), FVector2D(0.05f, 0.7f)}, true, Col, T);
			const float Drop = Warning == ETruckWarning::LowBeam ? 0.3f : 0.0f;
			for (int32 i = 0; i < 4; ++i)
			{
				const float Y = -0.52f + i * 0.35f;
				P.Shape(C, S, {FVector2D(-0.12f, Y), FVector2D(-0.92f, Y + Drop)}, false, Col, T);
			}
			break;
		}
		case ETruckWarning::ParkingBrake:
		case ETruckWarning::Abs:
		{
			P.Arc(C, S * 0.62f, 0.0f, 360.0f, Col, T, 3);
			P.Arc(C, S * 0.92f, 45.0f, 135.0f, Col, T, 3);
			P.Arc(C, S * 0.92f, 225.0f, 315.0f, Col, T, 3);
			if (Warning == ETruckWarning::ParkingBrake)
			{
				P.Shape(C, S, {FVector2D(-0.18f, 0.35f), FVector2D(-0.18f, -0.35f), FVector2D(0.1f, -0.35f), FVector2D(0.25f, -0.22f),
					FVector2D(0.25f, -0.05f), FVector2D(0.1f, 0.05f), FVector2D(-0.18f, 0.05f)}, false, Col, T);
			}
			else
			{
				P.Text(TEXT("ABS"), C, S * 0.5f, Col, true, 3);
			}
			break;
		}
		case ETruckWarning::CheckEngine:
			P.Shape(C, S, {FVector2D(-0.55f, -0.25f), FVector2D(-0.3f, -0.25f), FVector2D(-0.3f, -0.45f), FVector2D(0.15f, -0.45f),
				FVector2D(0.15f, -0.25f), FVector2D(0.45f, -0.25f), FVector2D(0.6f, -0.05f), FVector2D(0.85f, -0.05f),
				FVector2D(0.85f, 0.35f), FVector2D(0.6f, 0.35f), FVector2D(0.45f, 0.55f), FVector2D(-0.55f, 0.55f),
				FVector2D(-0.55f, 0.3f), FVector2D(-0.85f, 0.3f), FVector2D(-0.85f, -0.05f), FVector2D(-0.55f, -0.05f)}, true, Col, T);
			break;
		case ETruckWarning::GlowPlug:
		{
			TArray<FVector2D> Coil;
			Coil.Add(C + FVector2D(-0.85f, 0.55f) * S);
			for (int32 i = 0; i <= 24; ++i)
			{
				const float A = (float)i / 24.0f;
				Coil.Add(C + FVector2D(-0.85f + 1.7f * A, -0.35f * FMath::Sin(A * PI * 6.0f)) * S);
			}
			Coil.Add(C + FVector2D(0.85f, 0.55f) * S);
			P.Lines(Coil, Col, T, 3);
			break;
		}
		case ETruckWarning::Battery:
			P.Shape(C, S, {FVector2D(-0.8f, -0.35f), FVector2D(0.8f, -0.35f), FVector2D(0.8f, 0.6f), FVector2D(-0.8f, 0.6f)}, true, Col, T);
			P.Shape(C, S, {FVector2D(-0.5f, -0.35f), FVector2D(-0.5f, -0.55f), FVector2D(-0.25f, -0.55f), FVector2D(-0.25f, -0.35f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.25f, -0.35f), FVector2D(0.25f, -0.55f), FVector2D(0.5f, -0.55f), FVector2D(0.5f, -0.35f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(-0.55f, 0.12f), FVector2D(-0.25f, 0.12f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.25f, 0.12f), FVector2D(0.55f, 0.12f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.4f, -0.03f), FVector2D(0.4f, 0.27f)}, false, Col, T);
			break;
		case ETruckWarning::OilPressure:
			P.Shape(C, S, {FVector2D(-0.55f, -0.05f), FVector2D(0.15f, -0.05f), FVector2D(0.75f, -0.4f), FVector2D(0.9f, -0.3f),
				FVector2D(0.3f, 0.45f), FVector2D(-0.55f, 0.45f)}, true, Col, T);
			P.Shape(C, S, {FVector2D(-0.55f, 0.05f), FVector2D(-0.85f, -0.15f), FVector2D(-0.85f, 0.2f), FVector2D(-0.55f, 0.3f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(-0.25f, -0.05f), FVector2D(-0.25f, -0.25f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(-0.4f, -0.25f), FVector2D(-0.1f, -0.25f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.9f, 0.0f), FVector2D(0.9f, 0.18f)}, false, Col, T);
			break;
		case ETruckWarning::CoolantTemp:
			P.Shape(C, S, {FVector2D(0.0f, -0.85f), FVector2D(0.0f, 0.2f)}, false, Col, T);
			P.Arc(C + FVector2D(0.0f, 0.38f) * S, S * 0.18f, 0.0f, 360.0f, Col, T, 3);
			P.Shape(C, S, {FVector2D(0.0f, -0.6f), FVector2D(0.28f, -0.6f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.0f, -0.3f), FVector2D(0.28f, -0.3f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(-0.95f, 0.75f), FVector2D(-0.7f, 0.62f), FVector2D(-0.45f, 0.75f), FVector2D(-0.25f, 0.65f)}, false, Col, T);
			P.Shape(C, S, {FVector2D(0.25f, 0.65f), FVector2D(0.45f, 0.75f), FVector2D(0.7f, 0.62f), FVector2D(0.95f, 0.75f)}, false, Col, T);
			break;
		case ETruckWarning::LowFuel:
			P.Shape(C, S, {FVector2D(-0.6f, -0.75f), FVector2D(0.2f, -0.75f), FVector2D(0.2f, 0.8f), FVector2D(-0.6f, 0.8f)}, true, Col, T);
			P.Shape(C, S, {FVector2D(-0.45f, -0.55f), FVector2D(0.05f, -0.55f), FVector2D(0.05f, -0.15f), FVector2D(-0.45f, -0.15f)}, true, Col, T);
			P.Shape(C, S, {FVector2D(0.2f, -0.35f), FVector2D(0.5f, -0.15f), FVector2D(0.5f, 0.45f), FVector2D(0.7f, 0.55f),
				FVector2D(0.85f, 0.35f), FVector2D(0.85f, -0.45f), FVector2D(0.65f, -0.7f)}, false, Col, T);
			break;
		case ETruckWarning::LowAdBlue:
			P.Shape(C, S, {FVector2D(0.0f, -0.85f), FVector2D(0.25f, -0.45f), FVector2D(0.5f, -0.05f), FVector2D(0.6f, 0.3f),
				FVector2D(0.5f, 0.6f), FVector2D(0.25f, 0.78f), FVector2D(0.0f, 0.82f), FVector2D(-0.25f, 0.78f), FVector2D(-0.5f, 0.6f),
				FVector2D(-0.6f, 0.3f), FVector2D(-0.5f, -0.05f), FVector2D(-0.25f, -0.45f)}, true, Col, T);
			P.Shape(C, S, {FVector2D(-0.38f, 0.3f), FVector2D(-0.15f, 0.18f), FVector2D(0.05f, 0.3f), FVector2D(0.25f, 0.18f),
				FVector2D(0.4f, 0.28f)}, false, Col, T);
			break;
		default:
			break;
		}
	}

	// maly rucickovy budik (nafta, AdBlue): 0 vlavo dole, 1/1 vpravo dole
	void DrawSmallGauge(const FGaugePainter& P, const FVector2D& C, float R, float Value, float Low, ETruckWarning Icon,
		const TCHAR* Title, bool bLampOn, bool bLit)
	{
		auto Angle = [](float T) { return FMath::Lerp(-120.0f, 120.0f, FMath::Clamp(T, 0.0f, 1.0f)); };
		const FLinearColor Ink = Dimmed(WhiteCol, bLit);

		P.Disc(C, R, FaceCol, 0);
		P.Arc(C, R, 0.0f, 360.0f, BezelCol, R * 0.06f, 1);
		P.Arc(C, R * 0.83f, Angle(0.0f), Angle(Low), Dimmed(RedCol, bLit), R * 0.09f, 1);
		for (int32 i = 0; i <= 4; ++i)
		{
			const FVector2D D = Dir(Angle(i / 4.0f));
			const float Len = (i % 2 == 0) ? 0.2f : 0.12f;
			P.Line(C + D * R * (0.88f - Len), C + D * R * 0.88f, Ink, R * 0.05f, 2);
		}
		P.Text(TEXT("0"), C + Dir(Angle(0.0f)) * R * 0.5f, R * 0.2f, Ink, true);
		P.Text(TEXT("1/1"), C + Dir(Angle(1.0f)) * R * 0.48f, R * 0.17f, Ink, true);
		DrawIcon(P, Icon, C + FVector2D(0.0f, R * 0.30f), R * 0.17f, bLampOn ? LampAmber : Dimmed(FLinearColor(0.7f, 0.72f, 0.76f, 0.9f), bLit));
		P.Text(Title, C + FVector2D(0.0f, R * 0.66f), R * 0.16f, Ink, true);

		const FVector2D N = Dir(Angle(Value));
		P.Line(C - N * R * 0.12f, C + N * R * 0.74f, NeedleCol, R * 0.07f, 4);
		P.Disc(C, R * 0.11f, HubCol, 5);
	}
}

UTruckGaugeWidget::UTruckGaugeWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// plny kruh (zaobleny stvorec s polomerom polovice vysky) a plny obdlznik
	CircleBrush.DrawAs = ESlateBrushDrawType::RoundedBox;
	CircleBrush.ImageType = ESlateBrushImageType::NoImage;
	CircleBrush.OutlineSettings.RoundingType = ESlateBrushRoundingType::HalfHeightRadius;
	CircleBrush.OutlineSettings.Width = 0.0f;
	CircleBrush.TintColor = FSlateColor(FLinearColor::White);

	SolidBrush.DrawAs = ESlateBrushDrawType::Image;
	SolidBrush.ImageType = ESlateBrushImageType::NoImage;
	SolidBrush.TintColor = FSlateColor(FLinearColor::White);
}

void UTruckGaugeWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetVisibility(ESlateVisibility::HitTestInvisible);
	ForceVolatile(true);
	ShownRpm = Rpm;
	ShownSpeed = SpeedKmh;
	ShownFuel = FuelLevel;
	ShownAdBlue = AdBlueLevel;
}

void UTruckGaugeWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (bDemoMode)
	{
		TickDemo(InDeltaTime);
	}
	BlinkTime += InDeltaTime;
	LampTestTime = FMath::Max(0.0f, LampTestTime - InDeltaTime);

	const float Smooth = FMath::Max(NeedleSmoothing, 0.1f);
	ShownRpm = FMath::FInterpTo(ShownRpm, (bIgnitionOn && bEngineRunning) ? Rpm : 0.0f, InDeltaTime, Smooth);
	ShownSpeed = FMath::FInterpTo(ShownSpeed, bIgnitionOn ? SpeedKmh : 0.0f, InDeltaTime, Smooth);
	ShownFuel = FMath::FInterpTo(ShownFuel, bIgnitionOn ? FuelLevel : 0.0f, InDeltaTime, Smooth * 0.4f);
	ShownAdBlue = FMath::FInterpTo(ShownAdBlue, bIgnitionOn ? AdBlueLevel : 0.0f, InDeltaTime, Smooth * 0.4f);
}

void UTruckGaugeWidget::TickDemo(float DeltaTime)
{
	DemoTime += DeltaTime;
	const float T = DemoTime;
	SpeedKmh = 50.0f + 35.0f * FMath::Sin(T * 0.25f);
	Rpm = 900.0f + 1500.0f * (0.5f + 0.5f * FMath::Sin(T * 0.8f));
	Gear = FMath::Clamp(1 + FMath::FloorToInt(SpeedKmh / 9.0f), 1, 12);
	FuelLevel = 0.55f + 0.42f * FMath::Sin(T * 0.07f);
	AdBlueLevel = 0.14f + 0.1f * FMath::Sin(T * 0.11f);
	AverageConsumption = 27.0f + 4.0f * FMath::Sin(T * 0.13f);
	OdometerKm += SpeedKmh * DeltaTime / 3600.0f;
	SetWarning(ETruckWarning::LowBeam, true);
	SetWarning(ETruckWarning::TurnLeft, FMath::Sin(T * 0.4f) > 0.5f);
	SetWarning(ETruckWarning::HighBeam, FMath::Sin(T * 0.3f) > 0.7f);
	SetWarning(ETruckWarning::GlowPlug, T < 3.0f);
	SetWarning(ETruckWarning::CheckEngine, FMath::Sin(T * 0.17f) > 0.9f);
}

void UTruckGaugeWidget::SetVehicleState(float InSpeedKmh, float InRpm, int32 InGear)
{
	SpeedKmh = InSpeedKmh;
	Rpm = InRpm;
	Gear = InGear;
}

void UTruckGaugeWidget::SetWarning(ETruckWarning Warning, bool bOn)
{
	if ((uint8)Warning >= (uint8)ETruckWarning::Count)
	{
		return;
	}
	const uint32 Bit = 1u << (uint32)Warning;
	WarningMask = bOn ? (WarningMask | Bit) : (WarningMask & ~Bit);
}

bool UTruckGaugeWidget::IsWarningOn(ETruckWarning Warning) const
{
	if (!bIgnitionOn || (uint8)Warning >= (uint8)ETruckWarning::Count)
	{
		return false;
	}
	if (LampTestTime > 0.0f)
	{
		return true;
	}
	const bool bSet = (WarningMask & (1u << (uint32)Warning)) != 0;
	switch (Warning)
	{
	case ETruckWarning::TurnLeft:
	case ETruckWarning::TurnRight:
		return bSet && FMath::Fmod(BlinkTime, 0.8f) < 0.45f;
	case ETruckWarning::Battery:
	case ETruckWarning::OilPressure:
		return bSet || !bEngineRunning;
	case ETruckWarning::LowFuel:
		return bSet || FuelLevel < LowFuelThreshold;
	case ETruckWarning::LowAdBlue:
		return bSet || AdBlueLevel < LowAdBlueThreshold;
	default:
		return bSet;
	}
}

void UTruckGaugeWidget::SetIgnition(bool bOn)
{
	if (bOn && !bIgnitionOn)
	{
		LampTestTime = 1.5f;
	}
	bIgnitionOn = bOn;
}

void UTruckGaugeWidget::SetEngineRunning(bool bRunning)
{
	bEngineRunning = bRunning;
}

void UTruckGaugeWidget::AddTrip(float DistanceKm, float FuelLiters)
{
	DistanceKm = FMath::Max(0.0f, DistanceKm);
	OdometerKm += DistanceKm;
	TripKm += DistanceKm;
	TripLiters += FMath::Max(0.0f, FuelLiters);
	if (TripKm > 0.05f)
	{
		AverageConsumption = TripLiters / TripKm * 100.0f;
	}
}

void UTruckGaugeWidget::ResetTrip()
{
	TripKm = 0.0f;
	TripLiters = 0.0f;
	AverageConsumption = 0.0f;
}

int32 UTruckGaugeWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	using namespace TruckGaugeDraw;
	LayerId = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	// rozlozenie: velky otackomer vpravo dole, vedla neho nafta (hore) a AdBlue (dole)
	const FVector2D Area = AllottedGeometry.GetLocalSize();
	const float R = FMath::Max(40.0f, (float)Area.Y * 0.16f * Scale);
	const float SmallR = R * 0.40f;
	const float Edge = R * 0.15f;
	const FVector2D C((float)Area.X - Edge - SmallR * 2.0f - R * 0.16f - R, (float)Area.Y - Edge - R);
	const FVector2D FuelC(C.X + R + R * 0.16f + SmallR, C.Y - SmallR * 1.1f);
	const FVector2D AdBlueC(FuelC.X, C.Y + SmallR * 1.1f);

	const FGaugePainter P{AllottedGeometry, OutDrawElements, LayerId + 1, CircleBrush, SolidBrush};
	const bool bLit = bIgnitionOn;
	const FLinearColor Ink = Dimmed(WhiteCol, bLit);
	const float MaxValue = FMath::Max(MaxRpm, 500.0f);
	auto RpmAngle = [MaxValue](float Value) { return -135.0f + 270.0f * FMath::Clamp(Value / MaxValue, 0.0f, 1.03f); };

	// cifernik otackomera: pasma, rysky, cisla (x100 ot/min)
	P.Disc(C, R, FaceCol, 0);
	P.Arc(C, R, 0.0f, 360.0f, BezelCol, R * 0.035f, 1);
	P.Arc(C, R * 0.905f, RpmAngle(GreenRpmFrom), RpmAngle(GreenRpmTo), Dimmed(GreenCol, bLit), R * 0.05f, 1);
	P.Arc(C, R * 0.905f, RpmAngle(RedRpmFrom), RpmAngle(MaxValue), Dimmed(RedCol, bLit), R * 0.05f, 1);
	P.Arc(C, R * 0.86f, -135.0f, 135.0f, Ink, R * 0.012f, 2);
	const int32 Steps = FMath::FloorToInt(MaxValue / 250.0f);
	for (int32 i = 0; i <= Steps; ++i)
	{
		const float Value = i * 250.0f;
		const bool bMajor = i % 2 == 0;
		const FVector2D D = Dir(RpmAngle(Value));
		const FLinearColor TickCol = Value >= RedRpmFrom ? Dimmed(RedCol, bLit) : Ink;
		P.Line(C + D * R * (0.86f - (bMajor ? 0.11f : 0.06f)), C + D * R * 0.86f, TickCol, R * (bMajor ? 0.022f : 0.012f), 2);
		if (bMajor)
		{
			P.Text(FString::FromInt(FMath::RoundToInt(Value / 100.0f)), C + D * R * 0.67f, R * 0.12f, Ink, true);
		}
	}

	// kontrolky priamo v cifernikoch: hore svetla a smerovky, pod nimi motor
	static const ETruckWarning RowA[] = {ETruckWarning::TurnLeft, ETruckWarning::LowBeam, ETruckWarning::HighBeam,
		ETruckWarning::ParkingBrake, ETruckWarning::TurnRight};
	static const ETruckWarning RowB[] = {ETruckWarning::CheckEngine, ETruckWarning::GlowPlug, ETruckWarning::Battery,
		ETruckWarning::OilPressure, ETruckWarning::CoolantTemp, ETruckWarning::Abs};
	for (int32 i = 0; i < (int32)UE_ARRAY_COUNT(RowA); ++i)
	{
		const ETruckWarning W = RowA[i];
		DrawIcon(P, W, C + FVector2D((i - 2) * R * 0.18f, -R * 0.40f), R * 0.072f, IsWarningOn(W) ? LampColor(W) : LampOffCol);
	}
	for (int32 i = 0; i < (int32)UE_ARRAY_COUNT(RowB); ++i)
	{
		const ETruckWarning W = RowB[i];
		DrawIcon(P, W, C + FVector2D((i - 2.5f) * R * 0.15f, -R * 0.22f), R * 0.062f, IsWarningOn(W) ? LampColor(W) : LampOffCol);
	}

	// dole v cifernikoch: digitalna rychlost, pocitadlo km, priemerna spotreba
	const FString SpeedText = bLit ? FString::FromInt(FMath::RoundToInt(FMath::Abs(ShownSpeed))) : FString(TEXT("--"));
	P.Text(SpeedText, C + FVector2D(0.0f, R * 0.33f), R * 0.28f, Ink, true);
	P.Text(TEXT("km/h"), C + FVector2D(0.0f, R * 0.52f), R * 0.085f, Ink, false);
	P.Rect(C + FVector2D(0.0f, R * 0.67f), FVector2D(R * 0.62f, R * 0.13f), OdoCol, 1);
	P.Text(FString::Printf(TEXT("%06d km"), FMath::Clamp(FMath::FloorToInt(OdometerKm), 0, 999999)),
		C + FVector2D(0.0f, R * 0.67f), R * 0.085f, Ink, false);
	const FString Average = AverageConsumption > 0.01f
		? FString::Printf(TEXT("\u00D8 %.1f l/100 km"), AverageConsumption)
		: FString(TEXT("\u00D8 --.- l/100 km"));
	P.Text(Average, C + FVector2D(0.0f, R * 0.84f), R * 0.08f, Ink, false);

	// rucicka otacok a stupen v strede
	const FVector2D N = Dir(RpmAngle(ShownRpm));
	P.Line(C - N * R * 0.14f, C + N * R * 0.80f, NeedleCol, R * 0.035f, 4);
	P.Disc(C, R * 0.135f, HubCol, 5);
	P.Arc(C, R * 0.135f, 0.0f, 360.0f, BezelCol, R * 0.02f, 6);
	const FString GearText = Gear < 0 ? FString(TEXT("R")) : (Gear == 0 ? FString(TEXT("N")) : FString::FromInt(Gear));
	P.Text(GearText, C, R * 0.17f, Ink, true, 7);

	// rucickove budiky nafty a AdBlue
	DrawSmallGauge(P, FuelC, SmallR, ShownFuel, LowFuelThreshold, ETruckWarning::LowFuel, TEXT("NAFTA"),
		IsWarningOn(ETruckWarning::LowFuel), bLit);
	DrawSmallGauge(P, AdBlueC, SmallR, ShownAdBlue, LowAdBlueThreshold, ETruckWarning::LowAdBlue, TEXT("ADBLUE"),
		IsWarningOn(ETruckWarning::LowAdBlue), bLit);

	return LayerId + 9;
}
