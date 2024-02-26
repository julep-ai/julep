import { CreateDoc as CreateDocType, AgentDefaultSettings as AgentDefaultSettingsType, FunctionDef as FunctionDefType, CreateToolRequest as CreateToolRequestType, Instruction as InstructionType } from './api/types';

type DocDict = {
    [K in keyof CreateDocType]: CreateDocType[K];
}

type DefaultSettingsDict = {
    [K in keyof AgentDefaultSettingsType]: AgentDefaultSettingsType[K];
}

type FunctionDefDict = {
    [K in keyof FunctionDefType]: FunctionDefType[K];
}

type ToolDict = {
    [K in keyof CreateToolRequestType]: CreateToolRequestType[K];
}

type InstructionDict = {
    [K in keyof InstructionType]: InstructionType[K];
}