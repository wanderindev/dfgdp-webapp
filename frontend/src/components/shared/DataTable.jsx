import React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
} from "@tanstack/react-table";

import { rankItem } from "@tanstack/match-sorter-utils";
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

// Helper to append an "actions" column if actions are provided
function maybeAppendActions(inferredCols, actions) {
  if (!actions || actions.length === 0) {
    return inferredCols;
  }

  const actionsColumn = {
    id: "actions",
    cell: ({ row }) => {
      const rowData = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {actions.map((action, index) => (
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
 * Generic DataTable component with optional:
 *  - Sorting
 *  - Manual pagination
 *  - Global filter input
 *  - Actions dropdown column
 */
const DataTable = ({
  data = [],
  columns = [],
  actions = [],         // for dropdown actions
  loading = false,

  // Filtering props
  globalFilter = "",
  setGlobalFilter = () => {},

  // Pagination props
  pageCount = 1,
  currentPage = 1,
  onPageChange = () => {},
}) => {
  // 1) Build final columns (append actions column, or infer columns if none passed)
  const finalColumns = React.useMemo(() => {
    // If we have custom columns, just append the actions column (if any).
    if (columns.length > 0) {
      return maybeAppendActions(columns, actions);
    }

    // Otherwise, infer columns from the data keys of the first row:
    if (data.length === 0) {
      return [];
    }

    const sampleRow = data[0];
    const inferredCols = Object.keys(sampleRow).map((key) => ({
      accessorKey: key,
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() =>
            column.toggleSorting(column.getIsSorted() === "asc")
          }
        >
          {key}
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
    }));

    return maybeAppendActions(inferredCols, actions);
  }, [columns, data, actions]);

  // 2) Set up the table instance
  const table = useReactTable({
    data,
    columns: finalColumns,

    // manual pagination, so we rely on parent to tell us pageCount / currentPage
    manualPagination: true,
    pageCount,

    // wire up table state
    state: {
      globalFilter,
      pagination: {
        pageIndex: currentPage - 1, // React Table is 0-based
        pageSize: 10,
      },
    },

    // wire up filtering
    globalFilterFn: (row, columnId, filterValue) => {
      const rowValue = row.getValue(columnId);
      // fuzzy matching via rankItem
      // noinspection JSUnresolvedReference
      return rankItem(String(rowValue), String(filterValue)).passed;
    },
    onGlobalFilterChange: setGlobalFilter,

    // wire up pagination changes
    onPaginationChange: (updaterOrValue) => {
      let newPageIndex;
      if (typeof updaterOrValue === "function") {
        // functional update
        const prevState = {
          pageIndex: currentPage - 1,
          pageSize: 10,
        };
        const nextState = updaterOrValue(prevState);
        newPageIndex = nextState.pageIndex;
      } else {
        // direct object
        newPageIndex = updaterOrValue.pageIndex;
      }
      // pass it back up as 1-based
      onPageChange(newPageIndex + 1);
    },

    // row models
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  // 3) Render
  return (
    <div className="space-y-4">
      {/* GLOBAL FILTER input */}
      <Input
        placeholder="Search..."
        value={globalFilter || ""}
        onChange={(e) => table.setGlobalFilter(e.target.value)}
        className="max-w-sm"
      />

      <div>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
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
