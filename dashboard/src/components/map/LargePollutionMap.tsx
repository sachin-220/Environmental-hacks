import React, { useState } from 'react';
import { PlumeData } from '../../types';
import { GooglePollutionMap } from './GooglePollutionMap';
import { OsmPollutionMap } from './OsmPollutionMap';
import { MapErrorBoundary } from './MapErrorBoundary';

interface LargePollutionMapProps {
  plumes: PlumeData | null;
}

export const LargePollutionMap: React.FC<LargePollutionMapProps> = ({ plumes }) => {
  const [provider, setProvider] = useState<'google' | 'osm'>('google');

  return (
    <MapErrorBoundary
      fallbackTitle="Map Visualization Notice"
      onFallback={() => setProvider(provider === 'google' ? 'osm' : 'google')}
    >
      {provider === 'google' ? (
        <GooglePollutionMap plumes={plumes} onSwitchProvider={setProvider} />
      ) : (
        <OsmPollutionMap plumes={plumes} onSwitchProvider={setProvider} />
      )}
    </MapErrorBoundary>
  );
};
