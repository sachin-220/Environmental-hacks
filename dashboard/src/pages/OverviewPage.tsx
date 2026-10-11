import React from 'react';
import { CurrentStateTiles } from '../components/metrics/CurrentStateTiles';
import { LargePollutionMap } from '../components/map/LargePollutionMap';
import { CleanForecastChart } from '../components/forecast/CleanForecastChart';
import { CleanAtmosphericState } from '../components/atmosphere/CleanAtmosphericState';
import { WhyAQIRisesClean } from '../components/explainability/WhyAQIRisesClean';
import { DynamicModeMonitor } from '../components/modes/DynamicModeMonitor';
import { SourceAttributionClean } from '../components/attribution/SourceAttributionClean';
import { PlumeClockClean } from '../components/plume/PlumeClockClean';

import {
  CurrentState,
  ForecastData,
  AttributionData,
  PlumeData,
  WhyAQIRisesData
} from '../types';

interface OverviewPageProps {
  state: CurrentState | null;
  forecast: ForecastData | null;
  attribution: AttributionData | null;
  plumes: PlumeData | null;
  whyData: WhyAQIRisesData | null;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  state,
  forecast,
  attribution,
  plumes,
  whyData
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* 1. Key Metrics - 5-6 Horizontal Tiles */}
      <CurrentStateTiles state={state} />

      {/* 2. Large Hero Pollution Map (55-65% Visual Dominance) */}
      <LargePollutionMap plumes={plumes} />

      {/* 3. Forecast + Atmospheric State Profiles */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        <CleanForecastChart forecast={forecast} />
        <CleanAtmosphericState state={state} />
      </div>

      {/* 4. Why AQI Rises + Dynamic Modes */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        <WhyAQIRisesClean whyData={whyData} />
        <DynamicModeMonitor />
      </div>

      {/* 5. Source Attribution + Regional Plume Clock */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <SourceAttributionClean attribution={attribution} />
        <PlumeClockClean plumes={plumes} />
      </div>
    </div>
  );
};
