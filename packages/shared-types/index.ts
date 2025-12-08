export interface Vulnerability {
    id: string;
    title: string;
    severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
    description: string;
    remediation?: string;
}

export interface Asset {
    id: string;
    type: 'DOMAIN' | 'IP' | 'SERVICE';
    value: string;
    tags: string[];
}
