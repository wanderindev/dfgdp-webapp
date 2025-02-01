import React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
} from "@tanstack/react-table";

import { ArrowUpDown, MoreHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import StatusFilterSelect from "@/components/shared/StatusFilterSelect.jsx";


// Helper to append an "actions" column if actions are provided
function maybeAppendActions(inferredCols, actions) {
  if (!actions || actions.length === 0) {
    return inferredCols;
  }

  const actionsColumn = {
    id: "actions",
    cell: ({ row }) => {
      const rowData = row.original;

      // Filter actions based on shouldShow condition
      const visibleActions = actions.filter((action) =>
        action.shouldShow ? action.shouldShow(rowData) : true
      );

      if (visibleActions.length === 0) {
        return null;
      }

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {visibleActions.map((action, index) => (
              <DropdownMenuItem
                key={index}
                onClick={() => action.onClick?.(rowData)}
              >
                {action.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  };

  return [...inferredCols, actionsColumn];
}

/**
 * DataTable is a reusable table component that supports server-side pagination,
 * sorting, and filtering.
 *
 * @param {object} props - The component props.
 * @param {Array} [props.data=[]] - The array of data to be displayed in the table.
 * @param {Array} [props.columns=[]] - Column definitions for the table.
 * @param {Array} [props.actions=[]] - Additional actions to be rendered in the table.
 * @param {boolean} [props.loading=false] - If true, displays a loading indicator.
 *
 * // Columns Props:
 * @param {Array} [props.columnsOrder=[]] - Order in which columns should be displayed.
 * @param {Array} [props.columnsOverride] - Array of column override definitions.
 * @param {object} [props.columnWidths={}] - An object mapping column IDs to their widths.
 *
 * // Filtering Props:
 * @param {string} [props.globalFilter=""] - Global filter value.
 * @param {Function} [props.setGlobalFilter] - Callback to update the global filter.
 *
 * // Pagination Props:
 * @param {number} [props.pageCount=1] - Total number of pages available.
 * @param {number} [props.currentPage=1] - The current active page (1-indexed).
 * @param {Function} [props.setCurrentPage] - Callback to update the current page.
 * @param {number} [props.pageSize=12] - Number of rows per page.
 *
 * // Status Filter Props:
 * @param {string} [props.statusFilter="ALL"] - The status filter value.
 * @param {Function} [props.setStatusFilter] - Callback to update the status filter.
 * @param {boolean} [props.showStatusFilter=false] - Whether to display the status filter UI.
 *
 * // Control Buttons:
 * @param {Array} [props.controlButtons=[]] - Array of custom control buttons to render.
 *
 * // Sorting Props:
 * @param {Array} [props.sorting=[]] - Current sorting configuration.
 * @param {Function} [props.setSorting] - Callback to update the sorting configuration.
 *
 * @returns {JSX.Element} The rendered DataTable component.
 */
const DataTable = ({
  data = [],
  columns = [],
  actions = [],
  loading = false,

  // Columns props
  columnsOrder = [],
  columnsOverride,
  columnWidths = {},

  // Filtering props
  globalFilter = "",
  setGlobalFilter = (value) => {return value},

  // Pagination props
  pageCount = 1,
  currentPage = 1,
  setCurrentPage = (value) => {return value},
  pageSize = 12,

   // Status filter
  statusFilter = "ALL",
  setStatusFilter = (value) => {return value},
  showStatusFilter = false,

  // Control buttons
  controlButtons = [],

  // Sorting props
  sorting = [],
  setSorting =(value) => {return value},
}) => {
  // Build final columns (append actions column, or infer columns if none passed)
  const finalColumns = React.useMemo(() => {
    // If we have custom columns, just append the actions column (if any).
    if (columns.length > 0) {
      return maybeAppendActions(columns, actions);
    }

    // Otherwise, infer columns from the data keys of the first row
    if (data.length === 0) {
      return [];
    }

    const sampleRow = data[0];

    // Create a map of column overrides for quick lookup
    const overrideMap = Object.fromEntries(
      columnsOverride.map((col) => [col.accessorKey, col])
    );

    // Infer columns and apply overrides where necessary
    let inferredCols = Object.keys(sampleRow).map((key) => {
      // If the column is in columnsOverride, use it
      if (overrideMap[key]) {
        return overrideMap[key];
      }

      // Otherwise, create a default column definition
      const formattedKey = key
        .replace(/_/g, " ")
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");

      return {
        accessorKey: key,
        header: () => (
          <Button
            variant="ghost"
            className="hover:bg-transparent focus:bg-transparent"
            onClick={() =>
              setSorting((prev) => {
                const existingSort = prev.find((s) => s.id === key);
                if (!existingSort) {
                  return [{ id: key, desc: false }];
                }
                return [{ id: key, desc: !existingSort.desc }];
              })
            }
          >
            {formattedKey}
            <ArrowUpDown className="ml-2 h-4 w-4 transition-transform hover:scale-110" />
          </Button>
        ),
      };
    });

    // Apply column order if specified
    if (columnsOrder.length > 0) {
      inferredCols = columnsOrder
        .map((key) => inferredCols.find((col) => col.accessorKey === key))
        .filter(Boolean);
    }

    return maybeAppendActions(inferredCols, actions);
  }, [columns, data, actions, columnsOrder, columnsOverride]);

  // Set up the table instance
  const table = useReactTable({
    data,
    columns: finalColumns,

    // Sorting
    manualSorting: true,
    onSortingChange: setSorting,

    // wire up table state
    state: {
      sorting,
      pagination: {
        pageIndex: currentPage - 1,
        pageSize: pageSize,
      },
    },

    // Filtering
    onGlobalFilterChange: setGlobalFilter,

    // Pagination
    manualPagination: true,
    pageCount,
    onPaginationChange: (updaterOrValue) => {
      let newPageIndex;
      if (typeof updaterOrValue === "function") {
        // functional update
        const prevState = {
          pageIndex: currentPage - 1,
          pageSize: pageSize,
        };
        const nextState = updaterOrValue(prevState);
        newPageIndex = nextState.pageIndex;
      } else {
        // direct object
        newPageIndex = updaterOrValue.pageIndex;
      }
      // pass it back up as 1-based
      setCurrentPage(newPageIndex + 1);
    },

    // Row models
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="space-y-4">

      {/* FILTERS ROW */}
      <div className="flex items-center justify-between space-y-2">
        {/* Left Section: Filters */}
        <div className="flex items-center space-x-2">
          {/* GLOBAL FILTER */}
          <Input
            placeholder="Search..."
            value={globalFilter || ""}
            onChange={(e) => table.setGlobalFilter(e.target.value)}
            className="max-w-sm"
          />

          {/* STATUS FILTER - Only Show If `statusFilter` Exists */}
          {showStatusFilter && (
            <StatusFilterSelect
              statusFilter={statusFilter}
              setStatusFilter={setStatusFilter}
            />
          )}
        </div>

        {/* Right Section: Control Buttons (If Any) */}
        {controlButtons.length > 0 && (
          <div className="flex items-center space-x-2">
            {controlButtons.map((button, index) => (
              <div key={index}>{button}</div>
            ))}
          </div>
        )}
      </div>

      <div>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className={columnWidths?.[header.id] || "min-w-[150px] px-4"}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={finalColumns.length}
                  className="h-24 text-center"
                >
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={finalColumns.length}
                  className="h-24 text-center"
                >
                  No data found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* PAGINATION BUTTONS */}
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage() || loading}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage() || loading}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default DataTable;
