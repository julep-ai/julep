namespace Tasks;

//
// STEP KINDS
//

alias WorkflowStepKind =
    ////////////////////
    /// Common steps ///
    ////////////////////

    | /** A step that runs a tool */
      "tool_call"
    | /** A step that runs a prompt */
      "prompt"
    | /** A step that evaluates an expression */
      "evaluate"
    | /** A step that signals that it needs more input before resuming */
      "wait_for_input"
    | /** log step */
      "log"
    
    ////////////////////////
    /// Doc search steps ///
    ////////////////////////

    | /** A step that can embed text */
      "embed"
    | /** A step that can search for documents (in the agents doc store only) */
      "search"
 
    ///////////////////////
    /// Key-value steps ///
    ///////////////////////

    | /** set step */
      "set"
    | /** get step */
      "get"
 
    ///////////////////////
    /// Iteration steps ///
    ///////////////////////

    | /** foreach step */
      "foreach"
    | /** map_reduce step */
      "map_reduce"
    | /** parallel step */
      "parallel"
 
    /////////////////////////
    /// Conditional steps ///
    /////////////////////////

    | /** switch step */
      "switch"
    | /** A step that runs a conditional */
      "if_else"

    //////////////////////////
    /// Other control flow ///
    //////////////////////////

    | /** sleep step */
      "sleep"
    | /** return step */
      "return"
    | /** A step that runs a subworkflow */
      "yield"
    | /** Throw an error */
      "error";