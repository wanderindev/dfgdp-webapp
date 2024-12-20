import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import DataTable, { columns } from '@/components/users/DataTable';
import UserEditDialog from '@/components/users/UserEditDialog';
import PasswordResetDialog from '@/components/users/PasswordResetDialog';
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
import { api } from '@/services/api';


export const UsersPage = () => {
  const { toast } = useToast();
  const [users, setUsers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [editingUser, setEditingUser] = React.useState(null);
  const [resettingPasswordFor, setResettingPasswordFor] = React.useState(null);
  const [pagination, setPagination] = React.useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
  });
  const [filters, setFilters] = React.useState({
    email: '',
  });
  const [confirmationDialog, setConfirmationDialog] = React.useState({
    open: false,
    title: '',
    description: '',
    action: null,
  });

  // Fetch users on mount and when filters/pagination change
  React.useEffect(() => {
    fetchUsers();
  }, [pagination.currentPage, filters.email]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await api.fetchUsers({
        page: pagination.currentPage,
        pageSize: 10,
        email: filters.email,
      });

      setUsers(data.users);
      setPagination({
        currentPage: data.current_page,
        totalPages: data.pages,
        totalItems: data.total,
      });
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
      fetchUsers();
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
      fetchUsers();
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
      fetchUsers();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to deactivate user. Please try again.",
      });
    }
  };

  const handlePageChange = (newPage) => {
    setPagination(prev => ({
      ...prev,
      currentPage: newPage,
    }));
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
    }));
    setPagination(prev => ({
      ...prev,
      currentPage: 1, // Reset to first page when filter changes
    }));
  };

  const showConfirmation = (title, description, action) => {
    setConfirmationDialog({
      open: true,
      title,
      description,
      action,
    });
  };

  const handleConfirm = () => {
    confirmationDialog.action?.();
    setConfirmationDialog({
      open: false,
      title: '',
      description: '',
      action: null,
    });
  };

  if (loading && !users.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Users Management</h1>
      </div>

      <DataTable
        data={users}
        columns={columns}
        pageCount={pagination.totalPages}
        currentPage={pagination.currentPage}
        onPageChange={handlePageChange}
        filters={filters}
        onFilterChange={handleFilterChange}
        loading={loading}
        onEdit={setEditingUser}
        onResetPassword={setResettingPasswordFor}
        onActivate={(user) =>
          showConfirmation(
            "Activate User",
            "Are you sure you want to activate this user?",
            () => handleActivate(user)
          )
        }
        onDeactivate={(user) =>
          showConfirmation(
            "Deactivate User",
            "Are you sure you want to deactivate this user?",
            () => handleDeactivate(user)
          )
        }
      />

      <UserEditDialog
        user={editingUser}
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        onSave={handleEditUser}
      />

      <PasswordResetDialog
        user={resettingPasswordFor}
        isOpen={!!resettingPasswordFor}
        onClose={() => setResettingPasswordFor(null)}
        onReset={handleResetPassword}
      />

      <AlertDialog
        open={confirmationDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmationDialog({
              open: false,
              title: '',
              description: '',
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
            <AlertDialogAction onClick={handleConfirm}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default UsersPage;