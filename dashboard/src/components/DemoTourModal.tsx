import React, { useState } from 'react';
import { Sparkles, ChevronRight, ChevronLeft, X } from 'lucide-react';
import { DemoStep } from '../types';

interface DemoTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  steps: DemoStep[];
  onSelectStep?: (targetSection: string) => void;
}

export const DemoTourModal: React.FC<DemoTourModalProps> = ({
  isOpen,
  onClose,
  steps,
  onSelectStep
}) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);

  if (!isOpen) return null;

  const defaultSteps: DemoStep[] = [
    {
      step: 1,
      title: "1. What is happening?",
      target_section: "STATE",
      narrative: "Delhi NCR is currently experiencing 'Very Poor' air quality with CPCB NAQI at 385 and PM2.5 elevated to 235.4 µg/m³. The airshed is characterized by calm winds (2.8 m/s) and severe atmospheric stagnation."
    },
    {
      step: 2,
      title: "2. Why is it happening?",
      target_section: "EXPLAIN",
      narrative: "Nocturnal radiational cooling has established a +1.76 K capping inversion lid, compressing the planetary boundary layer down to 869 m and dropping the ventilation coefficient to 672 m²/s. Like a sealed pressure cooker, urban emissions cannot disperse vertically."
    },
    {
      step: 3,
      title: "3. Where is it coming from?",
      target_section: "ATTRIBUTION",
      narrative: "Counterfactual sensitivity analysis attributes 42.5% to local urban emissions (vehicular transport & industry) and 37.8% to regional crop stubble burning in Punjab and Haryana, with 19.7% transboundary regional background."
    },
    {
      step: 4,
      title: "4. Plume Clock ETA",
      target_section: "PLUMES",
      narrative: "The agricultural plume clock tracks active upwind fire clusters from NASA FIRMS. Under current northwesterly transport velocities (~18.2 km/h), the primary stubble smoke plume is projected to arrive at Delhi airshed in approximately 13.5 hours."
    },
    {
      step: 5,
      title: "5. What will happen next?",
      target_section: "FORECAST",
      narrative: "The verified Rank-12 Koopman/DMDc spectral emulator projects a 72-hour forward trajectory in ~32.2 milliseconds. Analytical Lyapunov uncertainty bands (±1.96σ) bound the forecast as pollution peaks near 320 µg/m³."
    },
    {
      step: 6,
      title: "6. What can we do?",
      target_section: "MPC",
      narrative: "Decision-makers can explore multi-sector control levers across Low Cost, Balanced, and Aggressive strategies. The optimizer enforces strict ramp limits (-30%/h) and societal feasibility bounds."
    },
    {
      step: 7,
      title: "7. What does AERIS recommend?",
      target_section: "COMPARISON",
      narrative: "Under the Balanced policy, AERIS recommends a 28.5% transport curtailment and 40% stubble fire suppression, achieving an average -45.2 µg/m³ PM2.5 reduction and averting the severe pollution spike."
    },
    {
      step: 8,
      title: "8. Scientific Integrity & Verification",
      target_section: "TECHNICAL",
      narrative: "Unlike black-box models, AERIS is backed by a verified SVD Rank-12 operator (λ=0), Lyapunov-stabilized spectral radius ρ=1.0000, zero target leakage, and explicit provenance tags on every data point."
    }
  ];

  const tourSteps = steps && steps.length > 0 ? steps : defaultSteps;
  const active = tourSteps[currentIdx] || defaultSteps[0];

  const handleNext = () => {
    if (currentIdx < tourSteps.length - 1) {
      const nextIdx = currentIdx + 1;
      setCurrentIdx(nextIdx);
      if (onSelectStep) onSelectStep(tourSteps[nextIdx].target_section);
    } else {
      onClose();
    }
  };

  const handlePrev = () => {
    if (currentIdx > 0) {
      const prevIdx = currentIdx - 1;
      setCurrentIdx(prevIdx);
      if (onSelectStep) onSelectStep(tourSteps[prevIdx].target_section);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} color="#2563EB" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#111827' }}>AERIS Demonstration Tour</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="provenance-tag modelled">
              STAGE {currentIdx + 1} OF {tourSteps.length}
            </span>
            <span style={{ fontSize: '0.72rem', color: '#64748B', fontFamily: 'var(--font-mono)' }}>
              SECTION: {active.target_section}
            </span>
          </div>

          <h2 style={{ fontSize: '1.2rem', color: '#111827', fontWeight: 700 }}>
            {active.title}
          </h2>

          <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: '1.6', background: 'var(--bg-secondary)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            {active.narrative}
          </p>

          {/* Progress dots */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', margin: '6px 0' }}>
            {tourSteps.map((_, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setCurrentIdx(idx);
                  if (onSelectStep) onSelectStep(tourSteps[idx].target_section);
                }}
                style={{
                  width: idx === currentIdx ? '20px' : '6px',
                  height: '6px',
                  borderRadius: '3px',
                  background: idx === currentIdx ? '#2563EB' : '#CBD5E1',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              />
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="btn-clean"
            onClick={handlePrev}
            disabled={currentIdx === 0}
            style={{ opacity: currentIdx === 0 ? 0.4 : 1 }}
          >
            <ChevronLeft size={15} />
            <span>Previous</span>
          </button>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-clean" onClick={onClose}>
              Skip
            </button>
            <button className="btn-clean primary" onClick={handleNext}>
              <span>{currentIdx === tourSteps.length - 1 ? 'Finish Tour' : 'Next Stage'}</span>
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
