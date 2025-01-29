import React from 'react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown, MoreHorizontal, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
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
import { debounce } from "lodash";

export const columns = [
  {
    accessorKey: "email",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Email
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
  },
  {
    accessorKey: "full_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Full Name
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
  },
  {
    accessorKey: "active",
    header: "Status",
    cell: ({ row }) => {
      return row.getValue("active") ? (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <Check className="w-4 h-4 mr-1" />
          Active
        </span>
      ) : (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <X className="w-4 h-4 mr-1" />
          Inactive
        </span>
      );
    },
  },
  {
    id: "actions",
    cell: ({ row, table }) => {
      const user = row.original;
      const { onEdit, onActivate, onDeactivate, onResetPassword } = table.options.meta || {};

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit?.(user)}>
              Edit details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onResetPassword?.(user)}>
              Reset password
            </DropdownMenuItem>
            {user.active ? (
              <DropdownMenuItem
                className="text-red-600"
                onClick={() => onDeactivate?.(user)}
              >
                Deactivate
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem
                className="text-green-600"
                onClick={() => onActivate?.(user)}
              >
                Activate
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

const DataTable = ({
  data,
  pageCount,
  currentPage,
  onPageChange,
  filters,
  onFilterChange,
  loading = false,
  onEdit,
  onResetPassword,
  onActivate,
  onDeactivate,
}) => {
  const table = useReactTable({
    data,
    columns,
    pageCount,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    state: {
      pagination: {
        pageIndex: currentPage - 1,
        pageSize: 10,
      },
    },
    onPaginationChange: (updater) => {
      if (typeof updater === 'function') {
        const newState = updater({ pageIndex: currentPage - 1, pageSize: 10 });
        onPageChange(newState.pageIndex + 1);
      }
    },
    meta: {
      onEdit,
      onResetPassword,
      onActivate,
      onDeactivate,
    },
  });

  const debouncedFilter = React.useMemo(
    () =>
      debounce((value) => {
        onFilterChange?.('email', value);
      }, 300),
    [onFilterChange]
  );

  return (
    <div className="space-y-4">
      <Input
        placeholder="Filter users..."
        defaultValue={filters?.email}
        onChange={(event) => debouncedFilter(event.target.value)}
        className="max-w-sm"
      />

      <div>
        <Table>
          <TableHeader className="sticky top-0 bg-white z-10">
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
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
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
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

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