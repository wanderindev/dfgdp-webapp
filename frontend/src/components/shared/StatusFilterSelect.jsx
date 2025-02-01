import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";

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
