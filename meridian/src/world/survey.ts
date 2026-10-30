// "First Light" survey content per body (charter H and K): one guided route of
// three waypoints that shows the body's power, and three scan targets, placed
// at real geographic coordinates on the body's frame (daylit at EPOCH).
// Coordinates are reference values entered without a fetched source, so the
// targets are tagged 'estimated'. Pure data: no Three.js, no game imports.

import type { DataTag } from './bodies';

export interface RouteSpec {
  lat: number;
  lon: number;
  /** Arrival radius around the waypoint [m, gameplay]. */
  radius: number;
  label: string;
}

export interface ScanSpec {
  lat: number;
  lon: number;
  label: string;
  note: string;
  tag: DataTag;
}

export interface SurveySpec {
  /** The landing site is searched within maxKm (real kilometres) of this point. */
  landingNear: { lat: number; lon: number; maxKm: number };
  route: [RouteSpec, RouteSpec, RouteSpec];
  scans: [ScanSpec, ScanSpec, ScanSpec];
}

export const FIRST_LIGHT: Readonly<Record<string, SurveySpec>> = {
  // Skyborne Flight: coast crossing to a mountain summit beacon (New Zealand, late morning at EPOCH).
  earth: {
    landingNear: { lat: -42.74, lon: 170.99, maxKm: 45 },
    route: [
      { lat: -42.72, lon: 170.95, radius: 150, label: 'Tasman coast at Hokitika' },
      { lat: -43.39, lon: 170.18, radius: 150, label: 'Franz Josef Glacier valley' },
      { lat: -43.595, lon: 170.142, radius: 120, label: 'Aoraki / Mount Cook summit beacon' },
    ],
    scans: [
      { lat: -43.595, lon: 170.142, label: 'Aoraki / Mount Cook', note: "New Zealand's highest mountain (3,724 m), in the Southern Alps.", tag: 'estimated' },
      { lat: -43.47, lon: 170.18, label: 'Franz Josef Glacier', note: 'A glacier that descends from the Southern Alps almost to the rainforest near the sea.', tag: 'estimated' },
      { lat: -43.05, lon: 170.62, label: 'Alpine Fault', note: 'The Pacific and Australian plates meet along the western foot of the Alps.', tag: 'estimated' },
    ],
  },
  // Lunar Step: crevasse field crossing (Rima Ariadaeus, near Tranquility Base; the near side is lit at EPOCH).
  moon: {
    landingNear: { lat: 4.6, lon: 13.6, maxKm: 40 },
    route: [
      { lat: 5.2, lon: 13.7, radius: 60, label: 'South rim of Rima Ariadaeus' },
      { lat: 6.4, lon: 13.95, radius: 60, label: 'Rima Ariadaeus crossing' },
      { lat: 7.6, lon: 14.2, radius: 60, label: 'North rim beacon' },
    ],
    scans: [
      { lat: 0.674, lon: 23.473, label: 'Tranquility Base', note: 'Apollo 11 landing site (July 1969), Mare Tranquillitatis.', tag: 'estimated' },
      { lat: 6.4, lon: 14.0, label: 'Rima Ariadaeus', note: 'A straight rille about 300 km long, formed where the crust pulled apart.', tag: 'estimated' },
      { lat: 7.8, lon: 6.3, label: 'Hyginus crater', note: 'A rimless volcanic collapse crater on a chain of pits (Rima Hyginus).', tag: 'estimated' },
    ],
  },
  // Redline: canyon run between three relays (Ma'adim Vallis into Gusev crater, near Mars's subsolar point at EPOCH).
  mars: {
    landingNear: { lat: -27.0, lon: 181.2, maxKm: 80 },
    route: [
      { lat: -26.0, lon: 180.6, radius: 150, label: "Relay 1: Ma'adim Vallis head" },
      { lat: -21.0, lon: 177.5, radius: 150, label: "Relay 2: Ma'adim Vallis" },
      { lat: -16.5, lon: 176.0, radius: 150, label: 'Relay 3: Gusev crater rim' },
    ],
    scans: [
      { lat: -14.57, lon: 175.47, label: 'Spirit landing site', note: 'Mars Exploration Rover Spirit landed in Gusev crater in January 2004.', tag: 'estimated' },
      { lat: -21.0, lon: 177.5, label: "Ma'adim Vallis", note: 'A canyon about 700 km long that once fed water into Gusev crater.', tag: 'estimated' },
      { lat: -9.3, lon: 174.4, label: 'Apollinaris Mons', note: 'An eroded shield volcano north of Gusev crater.', tag: 'estimated' },
    ],
  },
};

/** Bodies with a First Light survey, in the progression order (Earth, Moon, Mars). */
export const SURVEY_BODIES: readonly string[] = ['earth', 'moon', 'mars'];
