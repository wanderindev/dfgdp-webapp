import React from 'react';
import { Plus } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import DataTable from '@/components/shared/DataTable';
import ConfirmationDialog from '@/components/shared/ConfirmationDialog';
import { TagDialog, TagStatus } from '@/components/content/TagComponents';
import { contentService } from '@/services/content';

export const TagsPage = () => {
  const { toast } = useToast();

  // Data state
  const [tags, setTags] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  // UI states
  const [editingTag, setEditingTag] = React.useState(null);
  const [confirmDialog, setConfirmDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Filtering, Sorting & Pagination state
  const [statusFilter, setStatusFilter] = React.useState('ALL');
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [sorting, setSorting] = React.useState([]); // e.g. [{ id: 'name', desc: false }]
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 12;

  // Fetch tags from the backend (including pagination, sorting & filtering params)
  const fetchTags = async () => {
    try {
      setLoading(true);
      const sortParam = sorting[0]?.id || "name";
      const direction = sorting[0]?.desc ? "desc" : "asc";
      const data = await contentService.getTags(
        currentPage,
        pageSize,
        statusFilter === 'ALL' ? null : statusFilter,
        globalFilter,
        sortParam,
        direction
      );

      setTags(data.tags || []);
      setTotalPages(data.pages || 1);
    } catch (error) {
      console.log("Failed to load tags:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load tags. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    (async () => {
      await fetchTags();
    })();
  }, [globalFilter, statusFilter, sorting, currentPage]);

  const handleSaveTag = async (tagData) => {
    try {
      if (tagData.id) {
        await contentService.updateTag(tagData.id, { name: tagData.name });
      } else {
        await contentService.createTag({ name: tagData.name });
      }
      toast({
        title: "Success",
        description: `Tag ${tagData.id ? 'updated' : 'created'} successfully`,
      });
      setEditingTag(null);
      await fetchTags();
    } catch (error) {
      console.log("Failed to save tag:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to ${tagData.id ? 'update' : 'create'} tag. Please try again.`,
      });
    }
  };

  const handleUpdateStatus = async (tag, newStatus) => {
    try {
      await contentService.updateTagStatus(tag.id, newStatus);
      toast({
        title: "Success",
        description: `Tag ${newStatus.toLowerCase()} successfully`,
      });
      await fetchTags();
    } catch (error) {
      console.log("Failed to update tag status:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to update tag status. Please try again.`,
      });
    }
  };

  const showConfirmDialog = (title, description, action) => {
    setConfirmDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  const tagActions = [
    {
      label: "Edit Tag",
      onClick: (tag) => setEditingTag(tag),
      shouldShow: () => true,
    },
    {
      label: "Approve",
      onClick: (tag) =>
        showConfirmDialog(
          "Approve Tag",
          "Are you sure you want to approve this tag?",
          () => handleUpdateStatus(tag, 'APPROVED')
        ),
      shouldShow: (tag) => tag.status !== 'APPROVED',
    },
    {
      label: "Reject",
      onClick: (tag) =>
        showConfirmDialog(
          "Reject Tag",
          "Are you sure you want to reject this tag?",
          () => handleUpdateStatus(tag, 'REJECTED')
        ),
      shouldShow: (tag) => tag.status !== 'REJECTED',
    },
    {
      label: "Mark as Pending",
      onClick: (tag) => handleUpdateStatus(tag, 'PENDING'),
      shouldShow: (tag) =>
        tag.status === 'APPROVED' || tag.status === 'REJECTED',
    },
  ];

  const columnsOrder = ["name", "status"];
  const columnsOverride = [
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <TagStatus status={row.getValue("status")} />,
    },
  ];

  const columnWidths = {
    status: "w-[500px]",
    actions: "w-[100px]",
  };

  const controlButtons = [
    <Button key="add" onClick={() => setEditingTag({})}>
      <Plus className="h-4 w-4 mr-2" />
      Add Tag
    </Button>,
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Tag Management</h1>
      </div>

      <DataTable
        data={tags}
        loading={loading}
        actions={tagActions}
        // Server-side pagination & sorting
        pageCount={totalPages}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        sorting={sorting}
        setSorting={setSorting}
        globalFilter={globalFilter}
        setGlobalFilter={setGlobalFilter}
        // Filters
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        showStatusFilter={true}
        // Column configuration
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        pageSize={pageSize}
        controlButtons={controlButtons}
      />

      <TagDialog
        tag={editingTag}
        isOpen={!!editingTag}
        onClose={() => setEditingTag(null)}
        onSave={handleSaveTag}
      />

      <ConfirmationDialog
        open={confirmDialog.open}
        title={confirmDialog.title}
        description={confirmDialog.description}
        onConfirm={() => {
          confirmDialog.action?.();
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          });
        }}
        onClose={() =>
          setConfirmDialog({
            open: false,
            title: '',
            description: '',
            action: null,
          })
        }
      />
    </div>
  );
};
