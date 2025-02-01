import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";

/**
 * StatusFilterSelect renders a dropdown select component for filtering
 * records by status.
 *
 * @param {object} props - The component props.
 * @param {string} props.statusFilter - The currently selected status filter value.
 * @param {Function} props.setStatusFilter - Callback function to update the status filter.
 *
 * @returns {JSX.Element} A select element with status options.
 */
function StatusFilterSelect({ statusFilter, setStatusFilter }) {
  return (
    <Select value={statusFilter} onValueChange={setStatusFilter}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select Status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="ALL">All</SelectItem>
        <SelectItem value="PENDING">Pending</SelectItem>
        <SelectItem value="APPROVED">Approved</SelectItem>
        <SelectItem value="REJECTED">Rejected</SelectItem>
      </SelectContent>
    </Select>
  );
}

export default StatusFilterSelect;
