import type { SharedRecord } from "@/lib/knowledge-base";

export interface CategoryRecord extends SharedRecord {
  categoryId?: string;
  name?: string;
  domain?: string;
  description?: string;
  aliases?: string[];
  active?: boolean;
  verificationStatus?: string;
  dataMode?: string;
}

export interface ProductRecord extends SharedRecord {
  productId?: string;
  productName?: string;
  categoryId?: string;
  category?: string;
  domain?: string;
  productFamily?: string;
  aliases?: string[];
  applications?: string[];
  materials?: string[];
  primaryStandardId?: string;
  linkedStandards?: string[];
  active?: boolean;
  verificationStatus?: string;
  dataMode?: string;
}

export interface StandardRecord extends SharedRecord {
  standardId?: string;
  isNumber?: string;
  title?: string;
  productFamily?: string;
  category?: string;
  domain?: string;
  status?: string | { state?: string };
  verificationStatus?: string;
  dataMode?: string;
  classification?: { domain?: string; category?: string; subcategory?: string; productGroup?: string };
  scope?: { summary?: string; includedProducts?: string[]; applications?: string[] };
  testingRequirements?: string[];
  requirementsCovered?: string[];
  provenance?: Record<string, unknown>;
}

export interface RelationshipRecord extends SharedRecord {
  relationshipId?: string;
  fromStandardId?: string;
  fromStandard?: string;
  toStandardId?: string;
  toStandard?: string;
  toTitle?: string;
  relationshipType?: string;
  reason?: string;
  applicability?: string;
  mandatory?: boolean | string | null;
  status?: string;
  category?: string;
  domain?: string;
  verificationStatus?: string;
  dataMode?: string;
}

export interface CertificationRecord extends SharedRecord {
  certificationId?: string;
  standardId?: string;
  productId?: string;
  isNumber?: string;
  title?: string;
  type?: string;
  scheme?: string;
  mandatory?: boolean | null;
  status?: string;
  authority?: string;
  sourceId?: string;
  sourceUrl?: string;
  sourceVerified?: boolean;
  category?: string;
  domain?: string;
  verificationStatus?: string;
  dataMode?: string;
}

export interface QcoRecord extends SharedRecord {
  qcoId?: string;
  name?: string;
  standardId?: string;
  standardIds?: string[];
  productIds?: string[];
  isNumber?: string;
  status?: string;
  ministry?: string;
  notificationDate?: string | null;
  effectiveDate?: string | null;
  sourceId?: string;
  sourceUrl?: string;
  sourceVerified?: boolean;
  category?: string;
  domain?: string;
  verificationStatus?: string;
  dataMode?: string;
}

export interface VersionRecord extends SharedRecord {
  versionRecordId?: string;
  recordType?: string;
  standardId?: string;
  isNumber?: string;
  title?: string;
  currentVersion?: string;
  reaffirmed?: string | null;
  amendments?: Array<string | Record<string, unknown>>;
  status?: string;
  category?: string;
  verificationStatus?: string;
  dataMode?: string;
}
