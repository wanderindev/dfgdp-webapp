import React from 'react';
import { Check, MoreHorizontal, X, FileEdit, BookOpen, History, Image } from 'lucide-react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import RichTextEditor from '@/components/ui/RichTextEditor';

// Status badge component
export const ResearchStatus = ({ status }) => {
  switch (status) {
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
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <span className="w-2 h-2 mr-1 rounded-full bg-yellow-400" />
          Pending
        </span>
      );
  }
};

// Research review dialog
export const ResearchReviewDialog = ({
  research,
  isOpen,
  onClose,
  onSave,
  onApprove,
  onReject,
  onMakePending,
}) => {
  const [content, setContent] = React.useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
  const lastSavedContentRef = React.useRef('');

  React.useEffect(() => {
    if (research) {
      setContent(research.content);
      lastSavedContentRef.current = research.content;
      setHasUnsavedChanges(false);
    }
  }, [research]);

  const handleSave = async () => {
    await onSave?.({ id: research.id, content });
    lastSavedContentRef.current = content;
    setHasUnsavedChanges(false);
  };

  const handleContentChange = (newContent) => {
    setContent(newContent);
    setHasUnsavedChanges(newContent !== lastSavedContentRef.current);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[90vw] h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Review Research for "{research?.suggestion?.title}"
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <RichTextEditor
            content={content}
            onChange={handleContentChange}
          />
        </div>

        <DialogFooter className="mt-4">
          <div className="flex justify-between w-full">
            <div className="space-x-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="default"
                  onClick={handleSave}
                  disabled={!hasUnsavedChanges}
                >
                  Save Changes
                </Button>
                {hasUnsavedChanges && (
                  <span className="text-sm text-muted-foreground">
                    * You have unsaved changes
                  </span>
                )}
              </div>
            </div>
            <div className="space-x-2">
              <Button
                variant="outline"
                onClick={onClose}
              >
                Close
              </Button>
              {research?.status !== 'APPROVED' && (
                <Button
                  variant="default"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => onApprove?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  Approve
                </Button>
              )}
              {research?.status !== 'REJECTED' && (
                <Button
                  variant="destructive"
                  onClick={() => onReject?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  Reject
                </Button>
              )}
              {(research?.status === 'APPROVED' || research?.status === 'REJECTED') && (
                <Button
                  variant="secondary"
                  onClick={() => onMakePending?.(research.id)}
                  disabled={hasUnsavedChanges}
                >
                  <History className="w-4 h-4 mr-2" />
                  Make Pending
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Research table
export const ResearchTable = ({
  data,
  loading,
  onReview,
  onGenerateArticle,
  onGenerateMedia,
  onStatusFilterChange,
  currentStatusFilter,
  onMakePending,
}) => {
  const columns = [
    {
      accessorKey: "suggestion.title",
      header: "Article Title",
    },
    {
      accessorKey: "suggestion.level",
      header: "Level",
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <ResearchStatus status={row.getValue("status")} />,
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const research = row.original;
        const hasArticle = research.article !== null;
        const status = research.status;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onReview?.(research)}>
                <FileEdit className="h-4 w-4 mr-2" />
                Review Research
              </DropdownMenuItem>
              {status === 'APPROVED' && !research.article && (
                <>
                  <DropdownMenuItem onClick={() => onGenerateArticle?.(research)}>
                    <BookOpen className="h-4 w-4 mr-2" />
                    Generate Article
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onGenerateMedia?.(research)}>
                    <Image className="h-4 w-4 mr-2" />
                    Generate Media
                  </DropdownMenuItem>
                </>
              )}
              {(status === 'APPROVED' && !hasArticle || status === 'REJECTED') && (
                <DropdownMenuItem onClick={() => onMakePending?.(research.id)}>
                  <History className="h-4 w-4 mr-2" />
                  Make Pending
                </DropdownMenuItem>
              )}
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
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Select value={currentStatusFilter || ''} onValueChange={onStatusFilterChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="APPROVED">Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

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
                  No research items found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};