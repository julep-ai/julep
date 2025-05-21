export interface Transition {
  id: string;
  execution_id: string;
  type: string;
  step_label?: string | null;
  output: any;
  created_at: string;
}

export interface TransitionsQuery {
  transitions: Transition[];
}

export interface TransitionsStreamSubscription {
  transitions_stream: Transition[];
}
