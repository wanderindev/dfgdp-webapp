import React from 'react';
import { useToast } from "@/components/ui/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { CandidatesGrid, CandidateDetails } from '@/components/media/MediaCandidatesComponents';
import { contentService } from '@/services/content';

export const MediaCandidatesPage = () => {
  const { toast } = useToast();
  const [loading, setLoading] = React.useState(true);
  const [candidates, setCandidates] = React.useState([]);
  const [selectedCandidate, setSelectedCandidate] = React.useState(null);
  const [statusFilter, setStatusFilter] = React.useState('PENDING');

  // Fetch candidates on mount and when status filter changes
  React.useEffect(() => {
    fetchCandidates();
  }, [statusFilter]);

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const data = await contentService.getMediaCandidates(
        statusFilter === 'ALL' ? null : statusFilter
      );
      setCandidates(data || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load media candidates. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (candidateId, notes, createMedia) => {
    try {
      if (createMedia) {
        await contentService.approveCandidateAndCreateMedia(candidateId, notes);
        toast({
          title: "Success",
          description: "Candidate approved and added to media library",
        });
      } else {
        await contentService.updateCandidateStatus(candidateId, 'APPROVED', notes);
        toast({
          title: "Success",
          description: "Candidate approved successfully",
        });
      }
      setSelectedCandidate(null);
      fetchCandidates();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to approve candidate. Please try again.",
      });
    }
  };

  const handleReject = async (candidateId, notes) => {
    try {
      await contentService.updateCandidateStatus(candidateId, 'REJECTED', notes);
      toast({
        title: "Success",
        description: "Candidate rejected successfully",
      });
      setSelectedCandidate(null);
      fetchCandidates();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to reject candidate. Please try again.",
      });
    }
  };

  return (
    <div>
      <div className={`details-sidebar-layout ${selectedCandidate ? 'sidebar-open' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">Media Candidates</h1>
          <div className="flex items-center space-x-2">
            <Label>Status:</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select status"/>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All statuses</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <CandidatesGrid
            candidates={candidates}
            selectedId={selectedCandidate?.id}
            onSelect={setSelectedCandidate}
          />
        )}
      </div>

      {/* Details sidebar */}
      {selectedCandidate && (
        <div className="details-sidebar">
          <CandidateDetails
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </div>
      )}
    </div>
  );
};

export default MediaCandidatesPage;