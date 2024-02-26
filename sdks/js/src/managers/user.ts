import { User, CreateDoc, ResourceCreatedResponse, ResourceUpdatedResponse, ListUsersResponse } from "./api/types";
import { v4 as uuidv4 } from "uuid";
import { Observable, of } from "rxjs";

import { map, catchError } from "rxjs/operators";

import { BaseManager } from "./base";
import { isValidUuid } from "./utils";
import { DocDict } from "./types";

export class BaseUsersManager extends BaseManager {
  _get(id: string | UUID): User | Observable<User> {
    if (!isValidUuid(id)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.getUser(id);
  }

  _create(
    name: string,
    about: string,
    docs: DocDict[] = []
  ): Observable<ResourceCreatedResponse> {
    const docs$ = of(
      docs.map((doc) => new CreateDoc(doc))
    );

    return this.apiClient.createUser(name, about, docs$).pipe(
      map((response) => {
        return response;
      }),
      catchError((error) => {
        return of(error);
      })
    );
  }

  _listItems(
    limit?: number,
    offset?: number
  ): Observable<ListUsersResponse> {
    return this.apiClient.listUsers(limit, offset).pipe(
      map((response) => {
        return response;
      }),
      catchError((error) => {
        return of(error);
      })
    );
  }

  _delete(userId: string | UUID): Observable<void> {
    if (!isValidUuid(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.deleteUser(userId);
  }

  _update(
    userId: string | UUID,
    about?: string,
    name?: string
  ): Observable<ResourceUpdatedResponse> {
    if (!isValidUuid(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.updateUser(userId, about, name);
  }
}

export class UsersManager extends BaseUsersManager {
  get(id: string | UUID): User {
    return this._get(id);
  }

  create(
    name: string,
    about: string,
    docs: DocDict[] = []
  ): ResourceCreatedResponse {
    return this._create(name, about, docs);
  }

  list(limit?: number, offset?: number): User[] {
    return this._listItems(limit, offset).pipe(
      map((response) => {
        return response.items;
      })
    );
  }

  delete(userId: string | UUID): void {
    this._delete(userId);
  }

  update(
    userId: string | UUID,
    about?: string,
    name?: string
  ): ResourceUpdatedResponse {
    return this._update(userId, about, name);
  }
}

export class AsyncUsersManager extends BaseUsersManager {
  async get(id: string | UUID): Promise<User> {
    return await this._get(id);
  }

  async create(
    name: string,
    about: string,
    docs: DocDict[] = []
  ): Promise<ResourceCreatedResponse> {
    return await this._create(name, about, docs);
  }

  async list(
    limit?: number,
    offset?: number
  ): Promise<User[]> {
    return await this._listItems(limit, offset).pipe(
      map((response) => {
        return response.items;
      }),
      toArray()
    ).toPromise();
  }

  async delete(userId: string | UUID): Promise<void> {
    return await this._delete(userId);
  }

  async update(
    userId: string | UUID,
    about?: string,
    name?: string
  ): Promise<ResourceUpdatedResponse> {
    return await this._update(userId, about, name);
  }
}