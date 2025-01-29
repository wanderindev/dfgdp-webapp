import React from 'react';
import { Check, MoreHorizontal, X, BookOpen } from 'lucide-react';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// Status badge component
export const SuggestionStatus = ({ status }) => {
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

// Dialog for generating new suggestions
export const GenerateSuggestionsDialog = ({
  isOpen,
  onClose,
  onGenerate,
  taxonomies = []
}) => {
  const [formData, setFormData] = React.useState({
    taxonomyId: '',
    categoryId: '',
    count: 3
  });

  const selectedTaxonomy = taxonomies.find(t => t.id.toString() === formData.taxonomyId);
  // noinspection JSUnresolvedReference
  const categories = selectedTaxonomy?.categories || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Generate Article Suggestions</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="taxonomy">Taxonomy</Label>
            <Select
              value={formData.taxonomyId}
              onValueChange={(value) => setFormData(prev => ({
                ...prev,
                taxonomyId: value,
                categoryId: '' // Reset category when taxonomy changes
              }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a taxonomy" />
              </SelectTrigger>
              <SelectContent>
                {taxonomies.map((taxonomy) => (
                  <SelectItem key={taxonomy.id} value={taxonomy.id.toString()}>
                    {taxonomy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={formData.categoryId}
              onValueChange={(value) => setFormData(prev => ({
                ...prev,
                categoryId: value
              }))}
              disabled={!formData.taxonomyId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="count">Number of Suggestions</Label>
            <Input
              id="count"
              type="number"
              min="1"
              max="10"
              value={formData.count}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                count: parseInt(e.target.value, 10)
              }))}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!formData.taxonomyId || !formData.categoryId}
            >
              Generate
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Dialog for editing suggestions
export const SuggestionDialog = ({
  suggestion,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = React.useState({
    title: '',
    mainTopic: '',
    pointOfView: '',
    subTopics: '',
  });

  React.useEffect(() => {
    if (suggestion) {
      setFormData({
        title: suggestion.title || '',
        mainTopic: suggestion.mainTopic || '',
        pointOfView: suggestion.pointOfView || '',
        subTopics: suggestion.subTopics?.join('\n') || '',
      });
    }
  }, [suggestion]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      id: suggestion?.id,
      ...formData,
      subTopics: formData.subTopics.split('\n').filter(Boolean),
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[90vw] max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Edit Article Suggestion</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                title: e.target.value
              }))}
              placeholder="Enter article title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="mainTopic">Main Topic</Label>
            <Input
              id="mainTopic"
              value={formData.mainTopic}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                mainTopic: e.target.value
              }))}
              placeholder="Enter main topic"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subTopics">Sub Topics (one per line)</Label>
            <textarea
              id="subTopics"
              className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={formData.subTopics}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                subTopics: e.target.value
              }))}
              placeholder="Enter sub topics (one per line)"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pointOfView">Point of View</Label>
            <Input
              id="pointOfView"
              value={formData.pointOfView}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                pointOfView: e.target.value
              }))}
              placeholder="Enter point of view"
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// Data table for suggestions
export const SuggestionsTable = ({
   data,
   loading,
   onEdit,
   onGenerateResearch,
   onUpdateStatus,
   onStatusFilterChange,
   currentStatusFilter,
  }) => {
  const columns = [
    {
      accessorKey: "title",
      header: "Title",
    },
    {
      accessorKey: "mainTopic",
      header: "Main Topic",
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({row}) => <SuggestionStatus status={row.getValue("status")}/>,
    },
    {
      id: "actions",
      cell: ({row}) => {
        const suggestion = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit?.(suggestion)}>
                Edit suggestion
              </DropdownMenuItem>
              {suggestion.status === 'APPROVED' && !suggestion.research && (
                <DropdownMenuItem onClick={() => onGenerateResearch?.(suggestion)}>
                  <BookOpen className="h-4 w-4 mr-2" />
                  Generate Research
                </DropdownMenuItem>
              )}
              {suggestion.status !== 'APPROVED' && (
                <DropdownMenuItem
                  className="text-green-600"
                  onClick={() => onUpdateStatus?.(suggestion, 'APPROVED')}
                >
                  Approve
                </DropdownMenuItem>
              )}
              {suggestion.status !== 'REJECTED' && (
                <DropdownMenuItem
                  className="text-red-600"
                  onClick={() => onUpdateStatus?.(suggestion, 'REJECTED')}
                >
                  Reject
                </DropdownMenuItem>
              )}
              {(suggestion.status === 'APPROVED' || suggestion.status === 'REJECTED') && (
                <DropdownMenuItem
                  onClick={() => onUpdateStatus?.(suggestion, 'PENDING')}
                >
                  Mark as Pending
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
        <Label>Status Filter:</Label>
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
                  No suggestions found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};