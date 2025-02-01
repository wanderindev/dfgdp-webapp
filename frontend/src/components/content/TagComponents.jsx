import React from 'react';
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';


// Dialog for adding/editing tags
export const TagDialog = ({
  tag,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = React.useState({
    name: '',
  });

  React.useEffect(() => {
    if (tag) {
      setFormData({
        name: tag.name || '',
      });
    } else {
      setFormData({
        name: '',
      });
    }
  }, [tag]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...(tag?.id ? { id: tag.id } : {}),
      ...formData
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {tag ? 'Edit Tag' : 'Add Tag'}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({
                ...prev,
                name: e.target.value
              }))}
              placeholder="Enter tag name"
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

// Tag status badge component
export const TagStatus = ({ status }) => {
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
