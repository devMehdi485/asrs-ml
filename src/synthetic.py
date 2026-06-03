"""
Générateur d'un jeu de données synthétique au format ASRS.

Sert à développer et valider le pipeline AVANT le téléchargement du vrai CSV
(ou si le téléchargement n'aboutit pas). Reproduit :
  - la double ligne d'en-tête caractéristique des exports ASRS ;
  - des narratives plausibles regroupées en archétypes d'incidents (pour que
    le clustering ait une structure à retrouver) ;
  - des métadonnées cohérentes (date, anomalie, phase de vol, aéronef…) ;
  - quelques rapports volontairement atypiques (signaux faibles).
"""
from __future__ import annotations

import csv
import random
import numpy as np

# Archétypes : (nom, anomalie, phases, fragments de narrative)
ARCHETYPES = {
    "runway_incursion": {
        "anomaly": "Ground Incursion Runway",
        "phases": ["Taxi", "Landing", "Takeoff"],
        "frags": [
            "we were cleared to taxi but another aircraft crossed the active runway",
            "ground control gave conflicting instructions and we nearly entered the runway without clearance",
            "low visibility on the taxiway led to confusion about hold short lines",
            "tower issued takeoff clearance while a vehicle was still on the runway",
        ],
    },
    "altitude_deviation": {
        "anomaly": "Deviation Altitude Excursion From Assigned Altitude",
        "phases": ["Climb", "Cruise", "Descent"],
        "frags": [
            "the autopilot failed to capture the assigned altitude and we overshot by several hundred feet",
            "we received a traffic alert after deviating from our cleared altitude during climb",
            "distraction in the cockpit caused us to level off at the wrong altitude",
            "atc questioned our altitude after a misset altitude alerter",
        ],
    },
    "engine_mechanical": {
        "anomaly": "Aircraft Equipment Problem Critical",
        "phases": ["Climb", "Cruise", "Takeoff"],
        "frags": [
            "we observed abnormal engine vibration and a rising exhaust gas temperature",
            "an engine oil pressure warning illuminated and we declared an emergency",
            "a hydraulic system failure required us to run the abnormal checklist",
            "loss of thrust on one engine forced an air turn back to the departure airport",
        ],
    },
    "weather_turbulence": {
        "anomaly": "Inflight Event Weather Turbulence",
        "phases": ["Cruise", "Descent"],
        "frags": [
            "severe turbulence was encountered in convective weather and a flight attendant was injured",
            "we deviated around a line of thunderstorms but hit unexpected wind shear",
            "icing accumulated rapidly on the wings during the descent into the terminal area",
            "moderate to severe clear air turbulence caused loose items to fly about the cabin",
        ],
    },
    "atc_communication": {
        "anomaly": "ATC Issue All Types Communication Breakdown",
        "phases": ["Cruise", "Descent", "Approach"],
        "frags": [
            "a frequency congestion issue led to a missed handoff and loss of communication",
            "we read back the wrong heading and the controller did not catch the error",
            "language and phraseology confusion caused a misunderstanding of the clearance",
            "a stuck microphone blocked the frequency for an extended period",
        ],
    },
    "gear_landing": {
        "anomaly": "Aircraft Equipment Problem Less Severe",
        "phases": ["Landing", "Approach"],
        "frags": [
            "the landing gear did not indicate down and locked so we executed a go around",
            "an unstable approach led to a hard landing and a tail strike concern",
            "we experienced a flap asymmetry on final and increased our approach speed",
            "a gear handle malfunction required manual extension before landing",
        ],
    },
    "bird_strike": {
        "anomaly": "Inflight Event Bird Animal Strike",
        "phases": ["Takeoff", "Climb", "Approach"],
        "frags": [
            "we ingested a bird shortly after rotation and noticed an engine surge",
            "a flock of birds crossed the approach path and one struck the windshield",
            "after a bird strike on departure we returned for an inspection of the airframe",
        ],
    },
    "fuel_management": {
        "anomaly": "Aircraft Equipment Problem Critical Fuel",
        "phases": ["Cruise", "Descent"],
        "frags": [
            "a fuel imbalance developed and we suspected a leak from the left tank",
            "lower than planned fuel remaining prompted a diversion to an alternate airport",
            "a fuel quantity indication discrepancy raised concern about total fuel on board",
        ],
    },
}

AIRCRAFT = ["B737-800", "A320", "CRJ-200", "B777-200", "EMB-145",
            "A321", "B757-200", "DHC-8"]
WEATHER = ["VMC", "IMC", "Marginal VMC", "Night IMC"]
DETECTOR = ["Person Flight Crew", "Automation", "ATC", "Person Maintenance"]

# Rapports volontairement atypiques (signaux faibles) — vocabulaire rare.
WEAK_SIGNALS = [
    ("Unmanned Aircraft Encounter",
     "we observed a small drone passing extremely close to the cockpit during final approach near a major metropolitan airport"),
    ("Laser Illumination Event",
     "a green laser was directed at the flight deck during the approach causing temporary visual impairment of the pilot flying"),
    ("Cyber Anomaly Navigation",
     "the gps position appeared to be spoofed showing the aircraft far from its actual location with multiple navigation discrepancies"),
    ("Cabin Air Quality Fume Event",
     "an unusual oily smell and visible haze filled the cabin and flight deck prompting use of oxygen masks and a precautionary diversion"),
]


def generate(path: str, n: int = 1200, seed: int = 42,
             start_year: int = 2015, end_year: int = 2024) -> str:
    """Génère un CSV synthétique au format ASRS (double en-tête)."""
    rng = random.Random(seed)
    np.random.seed(seed)

    # En-têtes à 2 niveaux : (catégorie, sous-champ)
    header_cat = ["", "Time / Date", "Aircraft 1", "Aircraft 1", "Environment",
                  "Events", "Events", "Assessments", "Report 1", "Report 2", "Report 1.1"]
    header_sub = ["ACN", "Date", "Make Model Name", "Flight Phase", "Flight Conditions",
                  "Anomaly", "Detector", "Primary Problem", "Narrative",
                  "Narrative", "Synopsis"]

    rows = []
    archetype_names = list(ARCHETYPES.keys())
    for i in range(n):
        # 5 % de signaux faibles
        if rng.random() < 0.05:
            anomaly, frag = rng.choice(WEAK_SIGNALS)
            phase = rng.choice(["Approach", "Cruise", "Climb"])
            narrative = frag + ". " + rng.choice([
                "this is highly unusual and not part of normal operations",
                "we filed a report given the rarity of the event",
            ])
            narrative2 = ""
            synopsis = anomaly
        else:
            name = rng.choice(archetype_names)
            arch = ARCHETYPES[name]
            anomaly = arch["anomaly"]
            phase = rng.choice(arch["phases"])
            f1, f2 = rng.sample(arch["frags"], 2)
            narrative = (f"During the {phase.lower()} phase {f1}. "
                         f"The flight crew followed procedures and ZZZ tower was advised.")
            narrative2 = (f"As the relief pilot I confirm that {f2}. "
                          f"We continued to ZZZ without further incident.")
            synopsis = f"{anomaly} during {phase}."

        # date aléatoire avec une légère tendance haussière des incidents récents
        year = int(np.clip(np.random.normal(
            (start_year + end_year) / 2 + 2, 2.5), start_year, end_year))
        month = rng.randint(1, 12)
        date = f"{year}{month:02d}"

        rows.append([
            100000 + i, date, rng.choice(AIRCRAFT), phase, rng.choice(WEATHER),
            anomaly, rng.choice(DETECTOR),
            rng.choice(["Ambiguous", "Human Factors", "Aircraft", "Procedure", "Weather"]),
            narrative, narrative2, synopsis,
        ])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header_cat)
        w.writerow(header_sub)
        w.writerows(rows)
    return path


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "data", "ASRS_export.csv")
    generate(out)
    print("CSV synthétique généré :", out)
