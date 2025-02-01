import React from "react";
import { useToast } from "@/components/ui/use-toast";
import DataTable from "@/components/shared/DataTable";
import UserEditDialog from "@/components/users/UserEditDialog";
import PasswordResetDialog from "@/components/users/PasswordResetDialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { api } from "@/services/api";
import {Check, X} from "lucide-react";

export const UsersPage = () => {
  const { toast } = useToast();

  // -- STATE --
  const [users, setUsers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [editingUser, setEditingUser] = React.useState(null);
  const [resettingPasswordFor, setResettingPasswordFor] = React.useState(null);

  // For pagination:
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const pageSize = 12;

  // For filtering:
  const [globalFilter, setGlobalFilter] = React.useState("");

  //For sorting:
  const [sorting, setSorting] = React.useState([]);

  // For confirmation dialog:
  const [confirmationDialog, setConfirmationDialog] = React.useState({
    open: false,
    title: "",
    description: "",
    action: null,
  });

  // Re-fetch on mount, or when page/filter changes
  React.useEffect(() => {
    fetchUsers().catch(() => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Error fetching users.",
      });
    });
  }, [currentPage, sorting, globalFilter]);

  // -- HANDLERS --
  const fetchUsers = async () => {
    try {
      const sortParam = sorting[0]?.id || 'email'; // fallback
      const direction = sorting[0]?.desc ? 'desc' : 'asc';

      setLoading(true);
      const data = await api.fetchUsers({
        page: currentPage,
        pageSize,
        email: globalFilter,
        sort: sortParam,
        dir: direction,
      });

      setUsers(data.users);
      setTotalPages(data.pages)
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load users. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = async (userData) => {
    try {
      await api.updateUser(userData.id, userData);
      toast({
        title: "Success",
        description: "User updated successfully",
      });
      setEditingUser(null);
      await fetchUsers();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update user. Please try again.",
      });
    }
  };

  const handleResetPassword = async (password) => {
    try {
      await api.resetPassword(resettingPasswordFor.id, password);
      toast({
        title: "Success",
        description: "Password reset successfully",
      });
      setResettingPasswordFor(null);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to reset password. Please try again.",
      });
    }
  };

  const handleActivate = async (user) => {
    try {
      await api.activateUser(user.id);
      toast({
        title: "Success",
        description: "User activated successfully",
      });
      await fetchUsers();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to activate user. Please try again.",
      });
    }
  };

  const handleDeactivate = async (user) => {
    try {
      await api.deactivateUser(user.id);
      toast({
        title: "Success",
        description: "User deactivated successfully",
      });
      await fetchUsers();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to deactivate user. Please try again.",
      });
    }
  };

  const showConfirmationDialog = (title, description, action) => {
    setConfirmationDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  const handleConfirm = () => {
    confirmationDialog.action?.();
    setConfirmationDialog((prev) => ({
      ...prev,
      open: false,
      title: "",
      description: "",
      action: null,
    }));
  };

  // Defines the context menu for each user row
  const userActions = [
    {
      label: "Edit details",
      onClick: (user) => setEditingUser(user),
      shouldShow: () => true,
    },
    {
      label: "Reset password",
      onClick: (user) => setResettingPasswordFor(user),
      shouldShow: () => true,
    },
    {
      label: "Deactivate",
      onClick: (user) =>
        showConfirmationDialog("Deactivate user", "Are you sure?", () => handleDeactivate(user)),
      shouldShow: (user) => user.active,
    },
    {
      label: "Activate",
      onClick: (user) => handleActivate(user),
      shouldShow: (user) => !user.active,
    },
  ];

  // Define the columns props
  const columnsOrder = ["email", "full_name", "active"];
  const columnsOverride = [{
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
  }]
  const columnWidths = {
    email: "w-[500px]",
    full_name: "w-[500px]",
    active: "w-[500px]",
    actions: "w-[100px]",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Users Management</h1>
      </div>

      {/* Table */}
      <DataTable
        data={users}
        loading={loading}
        actions={userActions}
        pageCount={totalPages}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        pageSize={pageSize}
        globalFilter={globalFilter}
        setGlobalFilter={setGlobalFilter}
        columnsOrder={columnsOrder}
        columnsOverride={columnsOverride}
        columnWidths={columnWidths}
        sorting={sorting}
        setSorting={setSorting}
      />

      {/* Edit dialog */}
      <UserEditDialog
        user={editingUser}
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        onSave={handleEditUser}
      />

      {/* Password reset dialog */}
      <PasswordResetDialog
        user={resettingPasswordFor}
        isOpen={!!resettingPasswordFor}
        onClose={() => setResettingPasswordFor(null)}
        onReset={handleResetPassword}
      />

      {/* Confirmation Dialog */}
      <AlertDialog
        open={confirmationDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmationDialog({
              open: false,
              title: "",
              description: "",
              action: null,
            });
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmationDialog.title}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmationDialog.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
