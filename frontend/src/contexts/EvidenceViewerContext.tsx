import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";

interface EvidenceViewerContextType {
  isOpen: boolean;
  imageUrl: string | null;
  openModal: (url: string) => void;
  closeModal: () => void;
}

const EvidenceViewerContext = createContext<EvidenceViewerContextType | undefined>(
  undefined
);

export const EvidenceViewerProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  const openModal = useCallback((url: string) => {
    setImageUrl(url);
    setIsOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
    setImageUrl(null);
  }, []);

  return (
    <EvidenceViewerContext.Provider
      value={{ isOpen, imageUrl, openModal, closeModal }}
    >
      {children}
    </EvidenceViewerContext.Provider>
  );
};

export function useEvidenceViewer(): EvidenceViewerContextType {
  const context = useContext(EvidenceViewerContext);
  if (!context) {
    throw new Error(
      "useEvidenceViewer must be used within an EvidenceViewerProvider"
    );
  }
  return context;
}
