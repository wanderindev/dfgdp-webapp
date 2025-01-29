import React from 'react';
import { Check, X } from 'lucide-react';
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

// Status badge component
export const CandidateStatus = ({ status }) => {
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

// Grid of candidate thumbnails
export const CandidatesGrid = ({ candidates, onSelect, selectedId }) => {
  if (!candidates?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No candidates found.
      </div>
    );
  }

  // noinspection JSUnresolvedReference
  return (
    <div className="media-grid">
      {candidates.map((candidate) => (
        <Card
          key={candidate.id}
          className={`cursor-pointer hover:border-primary transition-colors ${
            selectedId === candidate.id ? 'border-primary' : ''
          }`}
          onClick={() => onSelect(candidate)}
        >
          <div className="aspect-square relative">
            <img
              src={candidate.commonsUrl}
              alt={candidate.title}
              className="absolute inset-0 w-full h-full object-cover"
            />
          </div>
          <CardContent className="p-2">
            <div className="truncate text-sm">{candidate.title}</div>
            <CandidateStatus status={candidate.status}/>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Candidate details sidebar
export const CandidateDetails = ({
  candidate,
  onClose,
  onApprove,
  onReject,
}) => {
  const [notes, setNotes] = React.useState("");
  const [showApprovalDialog, setShowApprovalDialog] = React.useState(false);

  if (!candidate) return null;

  const handleApprove = () => {
    setShowApprovalDialog(true);
  };

  const handleConfirmApproval = async (createMedia) => {
    await onApprove?.(candidate.id, notes, createMedia);
    setShowApprovalDialog(false);
    setNotes("");
  };

  const handleReject = async () => {
    await onReject?.(candidate.id, notes);
    setNotes("");
  };

  // noinspection JSUnresolvedReference
  return (
    <>
      <Card className="h-[calc(100vh_+_10px)] border-0">
        <CardHeader className="sticky top-0 z-10 bg-background px-4 py-3 -my-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-medium">Candidate Details</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="px-4">
          <div className="space-y-6">
            {/* Preview Image */}
            <div className="aspect-video relative">
              <img
                src={candidate.commonsUrl}
                alt={candidate.title}
                className="absolute inset-0 w-full h-full object-contain"
              />
            </div>

            {/* Metadata */}
            <div className="space-y-4">
              <div>
                <Label>Title</Label>
                <div className="text-sm mt-1">{candidate.title}</div>
              </div>

              {candidate.description && (
                <div>
                  <Label>Description</Label>
                  <div className="text-sm mt-1">{candidate.description}</div>
                </div>
              )}

              <div>
                <Label>Author</Label>
                <div className="text-sm mt-1">{candidate.author || 'Unknown'}</div>
              </div>

              <div>
                <Label>License</Label>
                <div className="text-sm mt-1">
                  <a
                    href={candidate.licenseUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {candidate.license}
                  </a>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Dimensions</Label>
                  <div className="text-sm mt-1">
                    {candidate.width} × {candidate.height}
                  </div>
                </div>
                <div>
                  <Label>Size</Label>
                  <div className="text-sm mt-1">
                    {Math.round(candidate.fileSize / 1024)} KB
                  </div>
                </div>
              </div>

              <div>
                <Label>Status</Label>
                <div className="mt-1">
                  <CandidateStatus status={candidate.status} />
                </div>
              </div>

              {/* Review Notes */}
              {candidate.status === 'PENDING' && (
                <div className="space-y-2">
                  <Label htmlFor="notes">Review Notes</Label>
                  <Input
                    id="notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add notes about this candidate..."
                  />
                </div>
              )}

              {/* Action Buttons */}
              {candidate.status === 'PENDING' && (
                <div className="flex space-x-2">
                  <Button
                    className="w-full"
                    onClick={handleApprove}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={handleReject}
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add to Media Library?</DialogTitle>
            <DialogDescription>
              Would you like to create a media entry for this image and add it to the library?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleConfirmApproval(false)}
            >
              Just Approve
            </Button>
            <Button
              onClick={() => handleConfirmApproval(true)}
            >
              Add to Library
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};