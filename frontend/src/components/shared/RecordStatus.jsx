import {Check, X} from "lucide-react";
import React from "react";

/**
 * RecordStatus displays a status label with an appropriate icon and color.
 *
 * @param {object} props - The component props.
 * @param {string} props.value - The status value, which can be one of:
 *   - "APPROVED"
 *   - "REJECTED"
 *   - "ACTIVE"
 *   - "INACTIVE"
 *   - or any other value (defaults to "Pending")
 *
 * @returns {JSX.Element} A styled span element representing the status.
 */
export const RecordStatus = ({ value }) => {
  switch (value) {
    case 'APPROVED':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <Check className="w-4 h-4 mr-1" />
          Approved
        </span>
      );
    case 'REJECTED':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <X className="w-4 h-4 mr-1" />
          Rejected
        </span>
      );
    case 'ACTIVE':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <Check className="w-4 h-4 mr-1" />
          Active
        </span>
      );
    case 'INACTIVE':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <X className="w-4 h-4 mr-1" />
          Inactive
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <span className="w-2 h-2 mr-1 rounded-full bg-yellow-400" />
          Pending
        </span>
      );
  }
};
