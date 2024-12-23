import React from 'react';
import { MoreHorizontal, Image } from 'lucide-react';
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable } from "@tanstack/react-table";
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

export const MediaSuggestionsTable = ({
  data,
  loading,
  onFetchCandidates,
}) => {
  // Helper function to format candidate counts
  const formatCandidateCounts = (candidates) => {
    if (!candidates || !candidates.length) return "No candidates";

    const counts = candidates.reduce((acc, candidate) => {
      acc[candidate.status] = (acc[candidate.status] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(counts)
      .map(([status, count]) => `${status}: ${count}`)
      .join(", ");
  };

  const columns = [
    {
      accessorKey: "research.suggestion.title",
      header: "Article Title",
    },
    {
      accessorKey: "searchQueries",
      header: "Search Queries",
      cell: ({ row }) => {
        const queries = row.getValue("searchQueries");
        return queries.length > 0 ? queries.join(", ") : "None";
      },
    },
    {
      accessorKey: "candidates",
      header: "Candidates",
      cell: ({ row }) => formatCandidateCounts(row.getValue("candidates")),
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const suggestion = row.original;
        const hasCandidates = suggestion.candidates && suggestion.candidates.length > 0;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onFetchCandidates?.(suggestion.id)}
                disabled={hasCandidates}
              >
                <Image className="h-4 w-4 mr-2" />
                {hasCandidates ? 'Candidates already fetched' : 'Fetch Candidates'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    }
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="rounded-md border">
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
                No media suggestions found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
};