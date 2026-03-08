#!/usr/bin/env npx ts-node
/**
 * CodeTrellis TypeScript Type Extractor
 *
 * Uses TypeScript Compiler API for accurate type extraction.
 * This script is called by the Python LSP extractor.
 *
 * Usage:
 *   npx ts-node extract-types.ts <project-path> [--output json|compact]
 *
 * Output:
 *   JSON with all interfaces, types, and their fully resolved definitions
 */

import * as fs from 'fs';
import * as path from 'path';
import * as ts from 'typescript';

// ============================================================================
// Types
// ============================================================================

interface PropertyInfo {
  name: string;
  type: string;
  optional: boolean;
  readonly: boolean;
  documentation?: string;
}

interface MethodInfo {
  name: string;
  parameters: { name: string; type: string; optional: boolean }[];
  returnType: string;
  documentation?: string;
}

interface InterfaceInfo {
  name: string;
  filePath: string;
  exported: boolean;
  properties: PropertyInfo[];
  methods: MethodInfo[];
  extends?: string[];
  generics?: string[];
  documentation?: string;
}

interface TypeAliasInfo {
  name: string;
  filePath: string;
  exported: boolean;
  definition: string;
  kind: 'union' | 'intersection' | 'object' | 'function' | 'primitive' | 'generic';
  documentation?: string;
}

interface ClassInfo {
  name: string;
  filePath: string;
  exported: boolean;
  properties: PropertyInfo[];
  methods: MethodInfo[];
  extends?: string;
  implements?: string[];
  decorators?: string[];
  documentation?: string;
  // Angular-specific
  isComponent?: boolean;
  isService?: boolean;
  isDirective?: boolean;
  isPipe?: boolean;
  inputs?: { name: string; type: string; required: boolean }[];
  outputs?: { name: string; type: string }[];
  selector?: string;
  injectables?: string[];
}

// Angular SignalStore info
interface StoreInfo {
  name: string;
  filePath: string;
  state: { name: string; type: string }[];
  computed: string[];
  methods: string[];
  features: string[];
}

interface ExtractionResult {
  projectPath: string;
  interfaces: InterfaceInfo[];
  types: TypeAliasInfo[];
  classes: ClassInfo[];
  stores: StoreInfo[];
  errors: string[];
  stats: {
    filesProcessed: number;
    interfacesFound: number;
    typesFound: number;
    classesFound: number;
    componentsFound: number;
    servicesFound: number;
    storesFound: number;
    processingTimeMs: number;
  };
}

// ============================================================================
// Type Extractor
// ============================================================================

class TypeExtractor {
  private program: ts.Program;
  private checker: ts.TypeChecker;
  private result: ExtractionResult;
  private processedFiles: Set<string> = new Set();

  constructor(projectPath: string) {
    // Try to find the best tsconfig - prefer tsconfig.app.json for Angular projects
    let configPath = ts.findConfigFile(projectPath, ts.sys.fileExists, 'tsconfig.app.json');

    // Fall back to tsconfig.json
    if (!configPath) {
      configPath = ts.findConfigFile(projectPath, ts.sys.fileExists, 'tsconfig.json');
    }

    if (!configPath) {
      throw new Error(`Could not find tsconfig.json in ${projectPath}`);
    }

    const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
    const parsedConfig = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      path.dirname(configPath),
    );

    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
    this.checker = this.program.getTypeChecker();

    this.result = {
      projectPath,
      interfaces: [],
      types: [],
      classes: [],
      stores: [],
      errors: [],
      stats: {
        filesProcessed: 0,
        interfacesFound: 0,
        typesFound: 0,
        classesFound: 0,
        componentsFound: 0,
        servicesFound: 0,
        storesFound: 0,
        processingTimeMs: 0,
      },
    };
  }

  extract(): ExtractionResult {
    const startTime = Date.now();

    for (const sourceFile of this.program.getSourceFiles()) {
      // Skip declaration files and node_modules
      if (sourceFile.isDeclarationFile) continue;
      if (sourceFile.fileName.includes('node_modules')) continue;
      if (sourceFile.fileName.includes('.spec.')) continue;
      if (sourceFile.fileName.includes('.test.')) continue;

      this.processedFiles.add(sourceFile.fileName);
      this.extractFromSourceFile(sourceFile);
      this.result.stats.filesProcessed++;
    }

    this.result.stats.processingTimeMs = Date.now() - startTime;
    this.result.stats.interfacesFound = this.result.interfaces.length;
    this.result.stats.typesFound = this.result.types.length;
    this.result.stats.classesFound = this.result.classes.length;
    this.result.stats.componentsFound = this.result.classes.filter((c) => c.isComponent).length;
    this.result.stats.servicesFound = this.result.classes.filter((c) => c.isService).length;
    this.result.stats.storesFound = this.result.stores.length;

    return this.result;
  }

  private extractFromSourceFile(sourceFile: ts.SourceFile): void {
    const visit = (node: ts.Node) => {
      try {
        if (ts.isInterfaceDeclaration(node)) {
          this.extractInterface(node, sourceFile);
        } else if (ts.isTypeAliasDeclaration(node)) {
          this.extractTypeAlias(node, sourceFile);
        } else if (ts.isClassDeclaration(node)) {
          this.extractClass(node, sourceFile);
        } else if (ts.isVariableStatement(node)) {
          // Check for signalStore declarations
          this.extractSignalStore(node, sourceFile);
        }
      } catch (error) {
        this.result.errors.push(`Error processing node in ${sourceFile.fileName}: ${error}`);
      }

      ts.forEachChild(node, visit);
    };

    visit(sourceFile);
  }

  private extractInterface(node: ts.InterfaceDeclaration, sourceFile: ts.SourceFile): void {
    const symbol = this.checker.getSymbolAtLocation(node.name);
    if (!symbol) return;

    const interfaceInfo: InterfaceInfo = {
      name: node.name.text,
      filePath: path.relative(this.result.projectPath, sourceFile.fileName),
      exported: this.hasExportModifier(node),
      properties: [],
      methods: [],
      documentation: this.getDocumentation(symbol),
    };

    // Extract generics
    if (node.typeParameters) {
      interfaceInfo.generics = node.typeParameters.map((tp) => tp.name.text);
    }

    // Extract extends
    if (node.heritageClauses) {
      for (const clause of node.heritageClauses) {
        if (clause.token === ts.SyntaxKind.ExtendsKeyword) {
          interfaceInfo.extends = clause.types.map((t) => t.expression.getText());
        }
      }
    }

    // Extract members
    for (const member of node.members) {
      if (ts.isPropertySignature(member)) {
        interfaceInfo.properties.push(this.extractProperty(member));
      } else if (ts.isMethodSignature(member)) {
        interfaceInfo.methods.push(this.extractMethod(member));
      }
    }

    this.result.interfaces.push(interfaceInfo);
  }

  private extractTypeAlias(node: ts.TypeAliasDeclaration, sourceFile: ts.SourceFile): void {
    const symbol = this.checker.getSymbolAtLocation(node.name);

    const type = this.checker.getTypeAtLocation(node.type);
    const typeString = this.checker.typeToString(
      type,
      node,
      ts.TypeFormatFlags.NoTruncation | ts.TypeFormatFlags.WriteArrayAsGenericType,
    );

    const typeInfo: TypeAliasInfo = {
      name: node.name.text,
      filePath: path.relative(this.result.projectPath, sourceFile.fileName),
      exported: this.hasExportModifier(node),
      definition: typeString,
      kind: this.getTypeKind(node.type),
      documentation: symbol ? this.getDocumentation(symbol) : undefined,
    };

    this.result.types.push(typeInfo);
  }

  private extractClass(node: ts.ClassDeclaration, sourceFile: ts.SourceFile): void {
    if (!node.name) return;

    const symbol = this.checker.getSymbolAtLocation(node.name);
    if (!symbol) return;

    const classInfo: ClassInfo = {
      name: node.name.text,
      filePath: path.relative(this.result.projectPath, sourceFile.fileName),
      exported: this.hasExportModifier(node),
      properties: [],
      methods: [],
      documentation: this.getDocumentation(symbol),
    };

    // Extract decorators and detect Angular types
    const decorators = ts.getDecorators(node);
    if (decorators) {
      classInfo.decorators = [];
      for (const decorator of decorators) {
        let decoratorName = '';
        if (ts.isCallExpression(decorator.expression)) {
          decoratorName = decorator.expression.expression.getText();
          classInfo.decorators.push(decoratorName);

          // Detect Angular decorator types
          if (decoratorName === 'Component') {
            classInfo.isComponent = true;
            classInfo.selector = this.extractDecoratorProperty(decorator, 'selector');
          } else if (decoratorName === 'Injectable') {
            classInfo.isService = true;
          } else if (decoratorName === 'Directive') {
            classInfo.isDirective = true;
            classInfo.selector = this.extractDecoratorProperty(decorator, 'selector');
          } else if (decoratorName === 'Pipe') {
            classInfo.isPipe = true;
          }
        } else {
          decoratorName = decorator.expression.getText();
          classInfo.decorators.push(decoratorName);
        }
      }
    }

    // Extract extends
    if (node.heritageClauses) {
      for (const clause of node.heritageClauses) {
        if (clause.token === ts.SyntaxKind.ExtendsKeyword) {
          classInfo.extends = clause.types[0]?.expression.getText();
        } else if (clause.token === ts.SyntaxKind.ImplementsKeyword) {
          classInfo.implements = clause.types.map((t) => t.expression.getText());
        }
      }
    }

    // Extract members with Angular-specific handling
    classInfo.inputs = [];
    classInfo.outputs = [];
    classInfo.injectables = [];

    for (const member of node.members) {
      if (ts.isPropertyDeclaration(member) && member.name) {
        const propInfo = this.extractClassProperty(member);
        classInfo.properties.push(propInfo);

        // Check for Angular decorators on property
        const memberDecorators = ts.getDecorators(member);
        if (memberDecorators) {
          for (const dec of memberDecorators) {
            if (ts.isCallExpression(dec.expression)) {
              const decName = dec.expression.expression.getText();
              if (decName === 'Input') {
                classInfo.inputs!.push({
                  name: propInfo.name,
                  type: propInfo.type,
                  required: false,
                });
              } else if (decName === 'Output') {
                classInfo.outputs!.push({
                  name: propInfo.name,
                  type: propInfo.type,
                });
              }
            }
          }
        }

        // Check for Angular 17+ signal inputs/outputs
        if (member.initializer) {
          const initText = member.initializer.getText();
          if (
            initText.startsWith('input(') ||
            initText.startsWith('input.required(') ||
            initText.startsWith('input<')
          ) {
            classInfo.inputs!.push({
              name: propInfo.name,
              type: propInfo.type,
              required: initText.includes('.required'),
            });
          } else if (initText.startsWith('output(') || initText.startsWith('output<')) {
            classInfo.outputs!.push({
              name: propInfo.name,
              type: propInfo.type,
            });
          }
        }

        // Check for inject() calls
        if (member.initializer && ts.isCallExpression(member.initializer)) {
          const callText = member.initializer.expression.getText();
          if (callText === 'inject') {
            const args = member.initializer.arguments;
            if (args.length > 0) {
              classInfo.injectables!.push(args[0].getText());
            }
          }
        }
      } else if (ts.isMethodDeclaration(member) && member.name) {
        classInfo.methods.push(this.extractClassMethod(member));
      } else if (ts.isConstructorDeclaration(member)) {
        // Extract constructor injection
        for (const param of member.parameters) {
          const paramDecorators = ts.getDecorators(param);
          if (param.type) {
            const typeName = param.type.getText();
            // Check if it's a dependency injection (has modifier or @Inject)
            if (
              param.modifiers?.some(
                (m) =>
                  m.kind === ts.SyntaxKind.PrivateKeyword ||
                  m.kind === ts.SyntaxKind.PublicKeyword ||
                  m.kind === ts.SyntaxKind.ProtectedKeyword,
              ) ||
              paramDecorators?.some((d) => d.expression.getText().includes('Inject'))
            ) {
              classInfo.injectables!.push(typeName);
            }
          }
        }
      }
    }

    this.result.classes.push(classInfo);
  }

  private extractDecoratorProperty(
    decorator: ts.Decorator,
    propertyName: string,
  ): string | undefined {
    if (!ts.isCallExpression(decorator.expression)) return undefined;
    const args = decorator.expression.arguments;
    if (args.length === 0) return undefined;

    const arg = args[0];
    if (ts.isObjectLiteralExpression(arg)) {
      for (const prop of arg.properties) {
        if (ts.isPropertyAssignment(prop) && prop.name.getText() === propertyName) {
          return prop.initializer.getText().replace(/['"]/g, '');
        }
      }
    }
    return undefined;
  }

  private extractSignalStore(node: ts.VariableStatement, sourceFile: ts.SourceFile): void {
    for (const declaration of node.declarationList.declarations) {
      if (!declaration.initializer) continue;
      if (!ts.isCallExpression(declaration.initializer)) continue;

      const callText = declaration.initializer.expression.getText();
      if (callText !== 'signalStore') continue;

      const storeName = declaration.name.getText();
      const storeInfo: StoreInfo = {
        name: storeName,
        filePath: path.relative(this.result.projectPath, sourceFile.fileName),
        state: [],
        computed: [],
        methods: [],
        features: [],
      };

      // Parse signalStore arguments
      for (const arg of declaration.initializer.arguments) {
        if (ts.isCallExpression(arg)) {
          const featureName = arg.expression.getText();
          storeInfo.features.push(featureName);

          // Extract state from withState
          if (featureName === 'withState' && arg.arguments.length > 0) {
            const stateArg = arg.arguments[0];
            if (ts.isObjectLiteralExpression(stateArg)) {
              for (const prop of stateArg.properties) {
                if (ts.isPropertyAssignment(prop)) {
                  const propType = this.checker.getTypeAtLocation(prop.initializer);
                  storeInfo.state.push({
                    name: prop.name.getText(),
                    type: this.checker.typeToString(propType),
                  });
                }
              }
            }
          }

          // Extract computed from withComputed
          if (featureName === 'withComputed' && arg.arguments.length > 0) {
            const computedArg = arg.arguments[0];
            if (ts.isArrowFunction(computedArg) || ts.isFunctionExpression(computedArg)) {
              const body = computedArg.body;
              if (ts.isParenthesizedExpression(body) || ts.isObjectLiteralExpression(body)) {
                const obj = ts.isParenthesizedExpression(body) ? body.expression : body;
                if (ts.isObjectLiteralExpression(obj)) {
                  for (const prop of obj.properties) {
                    if (ts.isPropertyAssignment(prop) || ts.isShorthandPropertyAssignment(prop)) {
                      storeInfo.computed.push(prop.name?.getText() || '');
                    }
                  }
                }
              }
            }
          }

          // Extract methods from withMethods
          if (featureName === 'withMethods' && arg.arguments.length > 0) {
            const methodsArg = arg.arguments[0];
            if (ts.isArrowFunction(methodsArg) || ts.isFunctionExpression(methodsArg)) {
              const body = methodsArg.body;
              if (ts.isParenthesizedExpression(body) || ts.isObjectLiteralExpression(body)) {
                const obj = ts.isParenthesizedExpression(body) ? body.expression : body;
                if (ts.isObjectLiteralExpression(obj)) {
                  for (const prop of obj.properties) {
                    if (ts.isPropertyAssignment(prop) || ts.isMethodDeclaration(prop)) {
                      storeInfo.methods.push(prop.name?.getText() || '');
                    }
                  }
                }
              }
            }
          }
        }
      }

      this.result.stores.push(storeInfo);
    }
  }

  private extractProperty(node: ts.PropertySignature): PropertyInfo {
    const name = node.name.getText();
    const type = node.type ? this.getFullTypeString(node.type) : 'any';

    return {
      name,
      type,
      optional: !!node.questionToken,
      readonly: node.modifiers?.some((m) => m.kind === ts.SyntaxKind.ReadonlyKeyword) ?? false,
    };
  }

  private extractClassProperty(node: ts.PropertyDeclaration): PropertyInfo {
    const name = node.name.getText();

    // Get the actual resolved type
    let type = 'any';
    if (node.type) {
      type = this.getFullTypeString(node.type);
    } else if (node.initializer) {
      // Infer type from initializer
      const inferredType = this.checker.getTypeAtLocation(node.initializer);
      type = this.checker.typeToString(inferredType);
    }

    return {
      name,
      type,
      optional: !!node.questionToken,
      readonly: node.modifiers?.some((m) => m.kind === ts.SyntaxKind.ReadonlyKeyword) ?? false,
    };
  }

  private extractMethod(node: ts.MethodSignature): MethodInfo {
    const name = node.name.getText();
    const parameters = node.parameters.map((p) => ({
      name: p.name.getText(),
      type: p.type ? this.getFullTypeString(p.type) : 'any',
      optional: !!p.questionToken,
    }));
    const returnType = node.type ? this.getFullTypeString(node.type) : 'void';

    return { name, parameters, returnType };
  }

  private extractClassMethod(node: ts.MethodDeclaration): MethodInfo {
    const name = node.name.getText();
    const parameters = node.parameters.map((p) => ({
      name: p.name.getText(),
      type: p.type ? this.getFullTypeString(p.type) : 'any',
      optional: !!p.questionToken,
    }));

    // Get return type - either declared or inferred
    let returnType = 'void';
    if (node.type) {
      returnType = this.getFullTypeString(node.type);
    } else {
      const signature = this.checker.getSignatureFromDeclaration(node);
      if (signature) {
        const inferredReturn = this.checker.getReturnTypeOfSignature(signature);
        returnType = this.checker.typeToString(inferredReturn);
      }
    }

    return { name, parameters, returnType };
  }

  private getFullTypeString(typeNode: ts.TypeNode): string {
    const type = this.checker.getTypeFromTypeNode(typeNode);
    return this.checker.typeToString(
      type,
      typeNode.parent,
      ts.TypeFormatFlags.NoTruncation |
        ts.TypeFormatFlags.WriteArrayAsGenericType |
        ts.TypeFormatFlags.UseFullyQualifiedType,
    );
  }

  private getTypeKind(typeNode: ts.TypeNode): TypeAliasInfo['kind'] {
    if (ts.isUnionTypeNode(typeNode)) return 'union';
    if (ts.isIntersectionTypeNode(typeNode)) return 'intersection';
    if (ts.isTypeLiteralNode(typeNode)) return 'object';
    if (ts.isFunctionTypeNode(typeNode)) return 'function';
    if (ts.isTypeReferenceNode(typeNode)) return 'generic';
    return 'primitive';
  }

  private hasExportModifier(node: ts.Node): boolean {
    const modifiers = ts.canHaveModifiers(node) ? ts.getModifiers(node) : undefined;
    return modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword) ?? false;
  }

  private getDocumentation(symbol: ts.Symbol): string | undefined {
    const docs = symbol.getDocumentationComment(this.checker);
    if (docs.length === 0) return undefined;
    return docs.map((d) => d.text).join('\n');
  }
}

// ============================================================================
// Main
// ============================================================================

function main(): void {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: npx ts-node extract-types.ts <project-path> [--output json|compact]');
    process.exit(1);
  }

  const projectPath = path.resolve(args[0]);
  const outputFormat = args.includes('--compact') ? 'compact' : 'json';

  if (!fs.existsSync(projectPath)) {
    console.error(`Project path does not exist: ${projectPath}`);
    process.exit(1);
  }

  try {
    const extractor = new TypeExtractor(projectPath);
    const result = extractor.extract();

    if (outputFormat === 'compact') {
      // Output in CodeTrellis-compatible format
      console.log(
        `# LSP Extraction: ${result.stats.filesProcessed} files, ${result.stats.componentsFound} components, ${result.stats.servicesFound} services, ${result.stats.storesFound} stores, ${result.stats.processingTimeMs}ms`,
      );
      console.log('');

      // Angular Components (from LSP)
      const components = result.classes.filter((c) => c.isComponent);
      if (components.length > 0) {
        console.log('[COMPONENTS:LSP]');
        for (const comp of components) {
          const inputs = comp.inputs?.map((i) => i.name).join(',') || '';
          const outputs = comp.outputs?.map((o) => o.name).join(',') || '';
          let line = `${comp.name}`;
          if (comp.selector) line += `|selector:${comp.selector}`;
          if (inputs) line += `|@in:${inputs}`;
          if (outputs) line += `|@out:${outputs}`;
          if (comp.injectables?.length) line += `|inject:[${comp.injectables.join(',')}]`;
          console.log(line);
        }
        console.log('');
      }

      // Angular Services (from LSP)
      const services = result.classes.filter((c) => c.isService);
      if (services.length > 0) {
        console.log('[ANGULAR_SERVICES:LSP]');
        for (const svc of services) {
          const injects = svc.injectables?.join(',') || '';
          const methods = svc.methods
            .slice(0, 15)
            .map((m) => m.name)
            .join(',');
          let line = `@Injectable class ${svc.name}`;
          if (injects) line += `|inject:[${injects}]`;
          if (methods) line += `|methods:[${methods}]`;
          console.log(line);
        }
        console.log('');
      }

      // SignalStores (from LSP)
      if (result.stores.length > 0) {
        console.log('[STORES:LSP]');
        for (const store of result.stores) {
          const features = store.features.join(',');
          const state = store.state.map((s) => s.name).join(',');
          const computed = store.computed.join(',');
          const methods = store.methods.join(',');
          let line = `signalStore ${store.name}|features:[${features}]`;
          if (state) line += `|state:[${state}]`;
          if (computed) line += `|computed:[${computed}]`;
          if (methods) line += `|methods:[${methods}]`;
          console.log(line);
        }
        console.log('');
      }

      console.log('[INTERFACES:LSP]');
      for (const iface of result.interfaces) {
        const props = iface.properties
          .map((p) => `${p.readonly ? 'readonly ' : ''}${p.name}${p.optional ? '?' : ''}:${p.type}`)
          .join(',');
        const methods = iface.methods
          .map(
            (m) =>
              `${m.name}(${m.parameters.map((p) => `${p.name}:${p.type}`).join(',')})=>${m.returnType}`,
          )
          .join(',');

        let line = `${iface.exported ? 'export|' : ''}interface ${iface.name}`;
        if (iface.generics) line += `<${iface.generics.join(',')}>`;
        if (iface.extends) line += ` extends ${iface.extends.join(',')}`;
        if (props) line += `|props:[${props}]`;
        if (methods) line += `|methods:[${methods}]`;
        console.log(line);
      }
      console.log('');

      console.log('[TYPES:LSP]');
      for (const type of result.types) {
        console.log(
          `${type.exported ? 'export|' : ''}type ${type.name}|kind:${type.kind}|def:${type.definition}`,
        );
      }
      console.log('');

      // Non-Angular classes
      const otherClasses = result.classes.filter(
        (c) => !c.isComponent && !c.isService && !c.isDirective && !c.isPipe,
      );
      if (otherClasses.length > 0) {
        console.log('[CLASSES:LSP]');
        for (const cls of otherClasses) {
          const decorators = cls.decorators ? `@${cls.decorators.join(',')}|` : '';
          const ext = cls.extends ? `extends:${cls.extends}|` : '';
          const impl = cls.implements ? `implements:${cls.implements.join(',')}|` : '';
          const props = cls.properties
            .slice(0, 10)
            .map((p) => p.name)
            .join(',');
          const methods = cls.methods
            .slice(0, 10)
            .map((m) => m.name)
            .join(',');

          console.log(
            `${decorators}${cls.exported ? 'export|' : ''}class ${cls.name}|${ext}${impl}props:[${props}]|methods:[${methods}]`,
          );
        }
      }
    } else {
      // Output full JSON
      console.log(JSON.stringify(result, null, 2));
    }
  } catch (error) {
    console.error(`Extraction failed: ${error}`);
    process.exit(1);
  }
}

main();
