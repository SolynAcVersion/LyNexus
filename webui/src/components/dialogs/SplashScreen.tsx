/**
 * SplashScreen Component
 * Loading screen shown during app initialization
 */

import { useEffect, useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { cn } from '../../utils/classnames';

// ============================================================================
// Type Definitions
// ============================================================================

interface SplashScreenProps {
  /**
   * Whether splash screen is visible
   */
  isVisible: boolean;
  /**
   * Loading progress (0-100)
   */
  progress?: number;
  /**
   * Current status message
   */
  status?: string;
  /**
   * Callback when splash screen should close
   */
  onComplete?: () => void;
}

// ============================================================================
// Loading Steps
// ============================================================================

const LOADING_STEPS = [
  { text: 'Loading configuration...', duration: 300 },
  { text: 'Loading chat history...', duration: 300 },
  { text: 'Initializing AI module...', duration: 300 },
  { text: 'Loading MCP tools...', duration: 300 },
  { text: 'Preparing user interface...', duration: 300 },
  { text: 'Ready!', duration: 200 },
];

// ============================================================================
// Main Component
// ============================================================================

/**
 * Splash screen with loading animation
 */
export function SplashScreen({
  isVisible,
  progress = 0,
  status = 'Initializing...',
  onComplete,
}: SplashScreenProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [currentProgress, setCurrentProgress] = useState(0);

  useEffect(() => {
    if (!isVisible) return;

    let timeout: NodeJS.Timeout;
    

    const steps = LOADING_STEPS.map((step, index) => ({
      ...step,
      progressStart: (index / LOADING_STEPS.length) * 100,
      progressEnd: ((index + 1) / LOADING_STEPS.length) * 100,
    }));

    const runStep = (stepIndex: number) => {
      if (stepIndex >= steps.length) {
        onComplete?.();
        return;
      }

      const step = steps[stepIndex];
      setCurrentStep(stepIndex);

      // Animate progress
      const progressInterval = setInterval(() => {
        setCurrentProgress((prev) => {
          const next = prev + 2;
          if (next >= step.progressEnd) {
            clearInterval(progressInterval);
            return step.progressEnd;
          }
          return next;
        });
      }, step.duration / 50);

      timeout = setTimeout(() => {
        clearInterval(progressInterval);
        runStep(stepIndex + 1);
      }, step.duration);
    };

    runStep(0);

    return () => {
      clearTimeout(timeout);
    };
  }, [isVisible, onComplete]);

  if (!isVisible) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-dark-bg',
        'transition-opacity duration-500',
        progress >= 100 && 'opacity-0 pointer-events-none'
      )}
    >
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-slow" />
          <div
            className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse-slow"
            style={{ animationDelay: '1s' }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
            <div className="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-primary-light flex items-center justify-center shadow-2xl">
              <Zap className="text-white" size={40} />
            </div>
          </div>
          <div className="text-left">
            <h1 className="text-4xl font-bold text-white">LyNexus</h1>
            <p className="text-dark-textSecondary">AI Assistant with MCP Tools</p>
          </div>
        </div>

        {/* Loading bar */}
        <div className="w-80 space-y-3">
          {/* Status text */}
          <p className="text-sm text-dark-textSecondary text-center">
            {LOADING_STEPS[currentStep]?.text || status}
          </p>

          {/* Progress bar */}
          <div className="h-1 bg-dark-bgTertiary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-300 ease-out"
              style={{ width: `${currentProgress}%` }}
            />
          </div>

          {/* Progress percentage */}
          <p className="text-xs text-dark-textTertiary text-center">
            {Math.round(currentProgress)}%
          </p>
        </div>

        {/* Loading indicator */}
        <div className="flex items-center gap-2 text-dark-textTertiary">
          <Loader2 size={16} className="animate-spin" />
          <span className="text-sm">Loading, please wait...</span>
        </div>
      </div>
    </div>
  );
}

export default SplashScreen;
