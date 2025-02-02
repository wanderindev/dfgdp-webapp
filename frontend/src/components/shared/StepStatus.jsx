import React from 'react';
import { Check } from 'lucide-react';

/**
 * StepStatus renders a small checkbox-like indicator.
 * It shows a checked box (with the Check icon) if done is true,
 * otherwise an empty square.
 *
 * @param {object} props
 * @param {boolean} props.done - Whether the step is completed.
 * @returns {JSX.Element}
 */
const StepStatus = ({ done }) => {
  if (done) {
    return (
      <div className="inline-flex items-center justify-center w-5 h-5 border rounded bg-green-500">
        <Check className="w-3 h-3 text-white" />
      </div>
    );
  }
  return (
    <div className="inline-flex items-center justify-center w-5 h-5 border rounded bg-white" />
  );
};

export default StepStatus;
